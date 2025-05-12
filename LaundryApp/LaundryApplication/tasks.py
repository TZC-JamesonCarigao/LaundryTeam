# import subprocess
# import re
# import time
# import socket
# from datetime import datetime, time as dt_time
# from django.utils import timezone
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
# from scheduler.models import Schedule, WiFiNetwork

# class WiFiConnectionManager:
#     def __init__(self, user):
#         self.user = user
#         self.current_ssid = None

#     def get_current_ssid(self):
#         try:
#             result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'],
#                                   capture_output=True, text=True, check=True)
#             match = re.search(r'SSID\s*:\s*(.+)', result.stdout)
#             if match:
#                 return match.group(1).strip()
#         except subprocess.CalledProcessError:
#             return None

#     def is_internet_available(self, timeout=3):
#         try:
#             socket.create_connection(("8.8.8.8", 53), timeout=timeout)
#             return True
#         except (socket.timeout, ConnectionError):
#             return False

#     def connect_to_wifi(self, ssid, password=None):
#         try:
#             # Disconnect first if needed
#             current_ssid = self.get_current_ssid()
#             if current_ssid:
#                 subprocess.run(['netsh', 'wlan', 'disconnect'], check=True)
#                 time.sleep(2)

#             # Connect command
#             if password:
#                 subprocess.run(['netsh', 'wlan', 'connect', f'name={ssid}', 'keyMaterial', password],
#                              check=True, timeout=30)
#             else:
#                 subprocess.run(['netsh', 'wlan', 'connect', f'name={ssid}'],
#                              check=True, timeout=30)

#             # Verify connection
#             if self._verify_connection(ssid):
#                 self.current_ssid = ssid
#                 return True
#         except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
#             pass
#         return False

#     def _verify_connection(self, expected_ssid, max_attempts=3, delay=5):
#         for _ in range(max_attempts):
#             current_ssid = self.get_current_ssid()
#             if current_ssid == expected_ssid and self.is_internet_available():
#                 return True
#             time.sleep(delay)
#         return False

# def run_scheduler():
#     while True:
#         now = timezone.now()
#         current_time = now.time()
        
#         active_schedules = Schedule.objects.filter(is_active=True)
        
#         for schedule in active_schedules:
#             # Check if it's time to switch to secondary
#             if (current_time.hour == schedule.switch_time.hour and 
#                 current_time.minute == schedule.switch_time.minute):
#                 if not _is_already_switched(schedule, now.date()):
#                     _switch_network(schedule, schedule.secondary_network, now)
            
#             # Check if it's time to revert to primary
#             elif (current_time.hour == schedule.revert_time.hour and 
#                   current_time.minute == schedule.revert_time.minute):
#                 if not _is_already_switched(schedule, now.date()):
#                     _switch_network(schedule, schedule.primary_network, now)
        
#         time.sleep(30)  # Check every 30 seconds

# def _is_already_switched(schedule, date):
#     # Check if we've already performed a switch today
#     from scheduler.models import SwitchLog
#     return SwitchLog.objects.filter(
#         schedule=schedule,
#         created_at__date=date
#     ).exists()

# def _switch_network(schedule, network, timestamp):
#     wifi_manager = WiFiConnectionManager(schedule.user)
#     success = wifi_manager.connect_to_wifi(network.ssid, network.password)
    
#     # Log the switch attempt
#     from scheduler.models import SwitchLog
#     SwitchLog.objects.create(
#         schedule=schedule,
#         network=network,
#         success=success,
#         created_at=timestamp
#     )
    
#     # Send real-time update
#     channel_layer = get_channel_layer()
#     async_to_sync(channel_layer.group_send)(
#         f"user_{schedule.user.id}",
#         {
#             "type": "switch.update",
#             "schedule_id": schedule.id,
#             "network": network.ssid,
#             "success": success,
#             "timestamp": timestamp.isoformat()
#         }
#     )
    
#     return success


#---2nd---
import subprocess
import re
import time
import socket
from datetime import datetime, timedelta
from django.utils import timezone
from .models import WiFiNetwork, Schedule, ConnectionLog

class WiFiConnectionManager:
    def __init__(self):
        self.current_ssid = None
        self.last_verified = None

    def get_current_ssid(self):
        """Get currently connected SSID with verification"""
        try:
            result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'],
                                  capture_output=True, text=True, check=True)
            match = re.search(r'SSID\s*:\s*(.+)', result.stdout)
            if match:
                self.current_ssid = match.group(1).strip()
                self.last_verified = timezone.now()
                return self.current_ssid
        except subprocess.CalledProcessError:
            pass
        return None

    def is_internet_available(self, timeout=3):
        """Check if internet access is available"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=timeout)
            return True
        except (socket.timeout, ConnectionError):
            return False

    def connect_to_wifi(self, ssid, password=None):
        """Connect to specified WiFi network with robust verification"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Disconnect first if needed
                current_ssid = self.get_current_ssid()
                if current_ssid:
                    subprocess.run(['netsh', 'wlan', 'disconnect'], check=True)
                    time.sleep(2)

                # Connect command
                cmd = ['netsh', 'wlan', 'connect', f'name={ssid}']
                if password:
                    cmd.extend(['keyMaterial', password])

                subprocess.run(cmd, check=True, timeout=30)

                # Enhanced verification
                if self._verify_connection(ssid):
                    self.current_ssid = ssid
                    return True

            except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
                time.sleep(5)  # Wait before retry

        return False

    def _verify_connection(self, expected_ssid, max_attempts=3, delay=5):
        """Thorough connection verification"""
        for _ in range(max_attempts):
            current_ssid = self.get_current_ssid()
            if current_ssid == expected_ssid and self.is_internet_available():
                return True
            time.sleep(delay)
        return False

    def log_message(self, message, is_success=False):
        """Log a message to the database"""
        ConnectionLog.objects.create(message=message, is_success=is_success)

def check_and_switch_wifi():
    """Check schedules and switch WiFi if needed"""
    wifi_manager = WiFiConnectionManager()
    now = timezone.now()
    current_time = now.time()
    today = now.date()

    active_schedules = Schedule.objects.filter(is_active=True)
    
    for schedule in active_schedules:
        # Check if it's time to switch to secondary
        if (current_time.hour == schedule.switch_time.hour and
                current_time.minute == schedule.switch_time.minute):

            if (not schedule.last_switch or 
                    schedule.last_switch.date() != today or
                    wifi_manager.get_current_ssid() != schedule.secondary_network.ssid):
                
                success = wifi_manager.connect_to_wifi(
                    schedule.secondary_network.ssid,
                    schedule.secondary_network.password
                )
                
                if success:
                    wifi_manager.log_message(
                        f"Switched to secondary WiFi: {schedule.secondary_network.ssid}",
                        is_success=True
                    )
                    schedule.last_switch = now
                    schedule.save()
                else:
                    wifi_manager.log_message(
                        f"Failed to switch to secondary WiFi: {schedule.secondary_network.ssid}",
                        is_success=False
                    )
                
                time.sleep(61)  # Prevent duplicate switches

        # Check if it's time to revert to primary
        elif (current_time.hour == schedule.revert_time.hour and
              current_time.minute == schedule.revert_time.minute):

            if (not schedule.last_switch or 
                    schedule.last_switch.date() != today or
                    wifi_manager.get_current_ssid() != schedule.primary_network.ssid):
                
                success = wifi_manager.connect_to_wifi(
                    schedule.primary_network.ssid,
                    schedule.primary_network.password
                )
                
                if success:
                    wifi_manager.log_message(
                        f"Reverted to primary WiFi: {schedule.primary_network.ssid}",
                        is_success=True
                    )
                    schedule.last_switch = now
                    schedule.save()
                else:
                    wifi_manager.log_message(
                        f"Failed to revert to primary WiFi: {schedule.primary_network.ssid}",
                        is_success=False
                    )
                
                time.sleep(61)  # Prevent duplicate switches