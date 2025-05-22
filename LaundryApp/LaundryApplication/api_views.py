from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from .models import WiFiNetwork, Schedule, ConnectionLog
from .tasks import wifi_schedule_manager

# Configure logger
logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def get_saved_networks(request):
    """API endpoint to get available WiFi networks"""
    try:
        network_list = []
        
        # Step 1: Get currently connected network
        from .tasks import WiFiConnectionManager
        manager = WiFiConnectionManager()
        current_ssid = manager.get_current_ssid()
        
        if current_ssid:
            logger.info(f"Current SSID detected: {current_ssid}")
            # Add current network to the list and database if needed
            current_net_in_db = WiFiNetwork.objects.filter(ssid=current_ssid).first()
            if current_net_in_db:
                network_list.append({
                    'id': current_net_in_db.id,
                    'ssid': current_ssid,
                    'isConnected': True,
                    'isSaved': True,
                    'isAvailable': True
                })
            else:
                network_list.append({
                    'id': 0,
                    'ssid': current_ssid,
                    'isConnected': True,
                    'isSaved': True,
                    'isAvailable': True
                })
                
                # Save to database
                WiFiNetwork.objects.create(
                    ssid=current_ssid,
                    password='',
                    is_primary=True
                )
        
        # Step 2: Get saved profiles from Windows using netsh
        import subprocess
        import platform
        import re
        
        if platform.system() == "Windows":
            try:
                # Get saved profiles
                profiles_output = subprocess.check_output(
                    ['netsh', 'wlan', 'show', 'profiles'], 
                    universal_newlines=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                # Extract profile names
                profile_matches = re.findall(r'All User Profile\s+:\s+(.+?)(?:\r|\n)', profiles_output)
                saved_profiles = [match.strip() for match in profile_matches if match.strip()]
                logger.info(f"Found {len(saved_profiles)} saved WiFi profiles")
                
                # Step 3: Get available networks
                networks_output = subprocess.check_output(
                    ['netsh', 'wlan', 'show', 'networks'], 
                    universal_newlines=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                # Extract SSID blocks from the output
                ssid_blocks = re.split(r'SSID \d+ : ', networks_output)[1:]
                
                # Process each SSID block
                available_networks = []
                for block in ssid_blocks:
                    lines = block.splitlines()
                    if lines:
                        ssid = lines[0].strip()
                        # Check if this network is visible (signal strength present)
                        is_available = any('Signal' in line for line in lines)
                        if ssid and is_available:
                            available_networks.append(ssid)
                
                logger.info(f"Found {len(available_networks)} available WiFi networks")
                
                # Step 4: Process all networks (saved and available)
                # Only include saved networks that are available
                for profile in saved_profiles:
                    if profile in available_networks:
                        db_network = WiFiNetwork.objects.filter(ssid=profile).first()
                        network_list.append({
                            'id': db_network.id if db_network else -1,
                            'ssid': profile,
                            'isConnected': profile == current_ssid,
                            'isSaved': True,
                            'isAvailable': True
                        })
                
                # Optionally, add the current network if it's not in saved_profiles but is available
                if current_ssid and current_ssid not in saved_profiles and current_ssid in available_networks:
                    db_network = WiFiNetwork.objects.filter(ssid=current_ssid).first()
                    network_list.append({
                        'id': db_network.id if db_network else -1,
                        'ssid': current_ssid,
                        'isConnected': True,
                        'isSaved': bool(db_network),
                        'isAvailable': True
                    })
            
            except Exception as e:
                logger.error(f"Error detecting networks with netsh: {str(e)}", exc_info=True)
        
        # Log the final network list
        logger.info(f"Returning {len(network_list)} network(s): {[n['ssid'] for n in network_list]}")
        return JsonResponse(network_list, safe=False)
        
    except Exception as e:
        logger.error(f"Error fetching networks: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_available_saved_networks(request):
    """
    API endpoint to get only saved WiFi networks that are currently available.
    For use by settings.html only.
    """
    try:
        import subprocess
        import platform
        import re

        network_list = []
        current_ssid = None
        debug_info = {}

        # Get current SSID using WiFiConnectionManager
        try:
            from .tasks import WiFiConnectionManager
            manager = WiFiConnectionManager()
            current_ssid = manager.get_current_ssid()
        except Exception:
            current_ssid = None

        if platform.system() == "Windows":
            # Get saved profiles
            profiles_output = subprocess.check_output(
                ['netsh', 'wlan', 'show', 'profiles'],
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )
            profile_matches = re.findall(r'All User Profile\s+:\s+(.+?)(?:\r|\n)', profiles_output)
            saved_profiles = [match.strip() for match in profile_matches if match.strip()]

            # Get available networks
            networks_output = subprocess.check_output(
                ['netsh', 'wlan', 'show', 'networks'],
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )
            ssid_blocks = re.split(r'SSID \d+ : ', networks_output)[1:]
            available_networks = []
            for block in ssid_blocks:
                lines = block.splitlines()
                if lines:
                    ssid = lines[0].strip()
                    is_available = any('Signal' in line for line in lines)
                    if ssid and is_available:
                        available_networks.append(ssid)

            # Debug info
            debug_info['saved_profiles'] = saved_profiles
            debug_info['available_networks'] = available_networks
            debug_info['current_ssid'] = current_ssid

            # Normalize for robust matching
            normalized_available = {a.strip().lower(): a.strip() for a in available_networks}
            for profile in saved_profiles:
                norm_profile = profile.strip().lower()
                if norm_profile in normalized_available:
                    db_network = WiFiNetwork.objects.filter(ssid=profile).first()
                    network_list.append({
                        'id': db_network.id if db_network else -1,
                        'ssid': profile,
                        'isConnected': profile == current_ssid,
                        'isSaved': True,
                        'isAvailable': True
                    })

            debug_info['matched_networks'] = [n['ssid'] for n in network_list]

        # ...add macOS/Linux support if needed...

        # If no networks found, return debug info for troubleshooting
        if not network_list:
            logger.warning("No networks found using automatic detection. Check system commands or network adapter.")
            return JsonResponse({
                "networks": [],
                "debug_info": debug_info,
                "error": "No networks detected. Check network adapter or permissions."
            })

        # Return the list (for frontend compatibility, just the array)
        return JsonResponse(network_list, safe=False)
    except Exception as e:
        logger.error(f"Error in get_available_saved_networks: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def start_schedule(request):
    """API endpoint to start a WiFi schedule"""
    try:
        # Parse request data
        data = json.loads(request.body)
        
        primary_wifi = data.get('primaryWifi')
        secondary_wifi = data.get('secondaryWifi')
        switch_time = data.get('switchTime')
        revert_time = data.get('revertTime')
        persist = data.get('persist', True)  # Default to persistent
        
        # Validate required fields
        if not all([primary_wifi, secondary_wifi, switch_time, revert_time]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required schedule parameters'
            }, status=400)
        
        # Get or create WiFi networks
        primary_network, _ = WiFiNetwork.objects.get_or_create(
            ssid=primary_wifi,
            defaults={'password': ''}
        )
        
        secondary_network, _ = WiFiNetwork.objects.get_or_create(
            ssid=secondary_wifi,
            defaults={'password': ''}
        )
        
        # Create or update schedule
        schedule, created = Schedule.objects.update_or_create(
            primary_network=primary_network,
            secondary_network=secondary_network,
            defaults={
                'switch_time': switch_time,
                'revert_time': revert_time,
                'is_active': True
            }
        )
        
        # Add to schedule manager
        success = wifi_schedule_manager.add_schedule(schedule)
        
        if success:
            # Log the action
            ConnectionLog.objects.create(
                message=f"Schedule started: {primary_wifi} ↔ {secondary_wifi}",
                is_success=True
            )
            
            return JsonResponse({
                'success': True,
                'schedule_id': schedule.id,
                'message': 'Schedule started successfully'
            })
        else:
            # Mark schedule as inactive and log error
            schedule.is_active = False
            schedule.save()
            
            ConnectionLog.objects.create(
                message=f"Failed to start schedule: {primary_wifi} ↔ {secondary_wifi}",
                is_success=False
            )
            
            return JsonResponse({
                'success': False,
                'error': 'Failed to start schedule'
            })
        
    except Exception as e:
        logger.error(f"Error starting schedule: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_http_methods(["POST"])
def stop_schedule(request):
    """API endpoint to stop all WiFi schedules"""
    try:
        # Stop all active schedules
        active_schedules = Schedule.objects.filter(is_active=True)
        
        for schedule in active_schedules:
            # Remove from schedule manager
            wifi_schedule_manager.remove_schedule(schedule.id)
            
            # Mark as inactive
            schedule.is_active = False
            schedule.save()
            
            # Log the action
            ConnectionLog.objects.create(
                message=f"Schedule stopped: {schedule.primary_network.ssid} ↔ {schedule.secondary_network.ssid}",
                is_success=True
            )
        
        return JsonResponse({
            'success': True,
            'message': 'All schedules stopped',
            'count': len(active_schedules)
        })
        
    except Exception as e:
        logger.error(f"Error stopping schedules: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_http_methods(["GET"])
def schedule_status(request):
    """API endpoint to check current schedule status"""
    try:
        # Get active schedules from database
        active_schedules = Schedule.objects.filter(is_active=True)
        
        if not active_schedules.exists():
            return JsonResponse({
                'active': False,
                'message': 'No active schedules'
            })
        
        # Get the first active schedule (assuming one active schedule at a time)
        active_schedule = active_schedules.first()
        
        # Get schedule details
        schedule_details = {
            'primaryWifi': active_schedule.primary_network.ssid,
            'secondaryWifi': active_schedule.secondary_network.ssid,
            'switchTime': active_schedule.switch_time,
            'revertTime': active_schedule.revert_time
        }
        
        # Get current connection
        from .tasks import WiFiConnectionManager
        current_ssid = WiFiConnectionManager().get_current_ssid()
        
        return JsonResponse({
            'active': True,
            'schedule': schedule_details,
            'current_ssid': current_ssid
        })
        
    except Exception as e:
        logger.error(f"Error checking schedule status: {str(e)}", exc_info=True)
        return JsonResponse({
            'active': False,
            'error': str(e)
        })
