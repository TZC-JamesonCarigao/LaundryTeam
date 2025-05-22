
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