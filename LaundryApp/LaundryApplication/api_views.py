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
        debug_info = {"debug_steps": []}

        # Add debug step
        debug_info["debug_steps"].append("Starting network detection")
        logger.info("Starting WiFi network detection")

        # Get current SSID using WiFiConnectionManager
        try:
            from .tasks import WiFiConnectionManager
            manager = WiFiConnectionManager()
            current_ssid = manager.get_current_ssid()
            debug_info["current_ssid_method_1"] = current_ssid
            logger.info(f"Current SSID detected via WiFiConnectionManager: {current_ssid}")
            debug_info["debug_steps"].append(f"Detected current SSID: {current_ssid}")
            
            # Alternative detection method if first method returns None
            if current_ssid is None:
                try:
                    # Use direct command execution
                    if platform.system() == "Windows":
                        result = subprocess.run(
                            ['netsh', 'wlan', 'show', 'interfaces'],
                            capture_output=True,
                            text=True,
                            encoding='utf-8',
                            errors='replace'
                        )
                        
                        # Try multiple regex patterns
                        patterns = [
                            r'SSID\s*:\s*(.*?)[\r\n]',
                            r'SSID\s+:\s+(.*?)[\r\n]',
                            r'Profile\s*:\s*(.*?)[\r\n]'
                        ]
                        
                        for pattern in patterns:
                            match = re.search(pattern, result.stdout)
                            if match and match.group(1).strip():
                                current_ssid = match.group(1).strip()
                                debug_info["current_ssid_method_2"] = current_ssid
                                debug_info["debug_steps"].append(f"Detected current SSID using alt method: {current_ssid}")
                                break
                except Exception as e:
                    debug_info["debug_steps"].append(f"Alt method failed: {str(e)}")
        except Exception as e:
            error_msg = f"Error detecting current SSID: {str(e)}"
            logger.error(error_msg)
            debug_info["current_ssid_error"] = str(e)
            debug_info["debug_steps"].append(error_msg)
            current_ssid = None

        os_name = platform.system()
        debug_info["os"] = os_name
        debug_info["debug_steps"].append(f"Detected OS: {os_name}")

        if platform.system() == "Windows":
            try:
                # Get saved profiles with better error handling
                debug_info["debug_steps"].append("Running 'netsh wlan show profiles' command")
                profiles_output = subprocess.check_output(
                    ['netsh', 'wlan', 'show', 'profiles'],
                    universal_newlines=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                # Log the raw command output for debugging
                logger.debug(f"Raw profiles output: {profiles_output[:200]}...")
                debug_info["raw_profiles_output"] = profiles_output[:500]
                
                # Extract profile names
                profile_matches = re.findall(r'All User Profile\s+:\s+(.+?)(?:\r|\n)', profiles_output)
                saved_profiles = [match.strip() for match in profile_matches if match.strip()]
                debug_info["saved_profiles"] = saved_profiles
                logger.info(f"Found {len(saved_profiles)} saved WiFi profiles: {saved_profiles}")
                debug_info["debug_steps"].append(f"Found {len(saved_profiles)} saved profiles")

                # Get available networks with better error handling
                debug_info["debug_steps"].append("Running 'netsh wlan show networks' command")
                networks_output = subprocess.check_output(
                    ['netsh', 'wlan', 'show', 'networks'],
                    universal_newlines=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                # Log the raw command output for debugging
                logger.debug(f"Raw networks output: {networks_output[:200]}...")
                debug_info["raw_networks_output"] = networks_output[:500]
                
                # Extract SSID blocks
                ssid_blocks = re.split(r'SSID \d+ : ', networks_output)[1:]
                debug_info["ssid_blocks_count"] = len(ssid_blocks)
                available_networks = []
                
                for block in ssid_blocks:
                    lines = block.splitlines()
                    if lines:
                        ssid = lines[0].strip()
                        # FIX: Look for any of these common strings instead of just "Signal"
                        # Different versions of Windows netsh have different output formats
                        is_available = any(keyword in block for keyword in ['Authentication', 'Network type', 'Encryption', 'Signal'])
                        if ssid and is_available:
                            available_networks.append(ssid)
                            debug_info["debug_steps"].append(f"Found available network: {ssid}")
                
                debug_info["available_networks"] = available_networks
                logger.info(f"Found {len(available_networks)} available WiFi networks: {available_networks}")
                debug_info["debug_steps"].append(f"Found {len(available_networks)} available networks")

                # Match saved profiles with available networks
                available_saved_networks = []
                for profile in saved_profiles:
                    if profile in available_networks:
                        # Check if network exists in database
                        db_network = WiFiNetwork.objects.filter(ssid=profile).first()
                        
                        # Create network entry
                        network_entry = {
                            'id': db_network.id if db_network else -1,
                            'ssid': profile,
                            'isConnected': profile == current_ssid,
                            'isSaved': True,
                            'isAvailable': True
                        }
                        available_saved_networks.append(network_entry)
                        debug_info["debug_steps"].append(f"Added network to results: {profile}")
                
                debug_info["matched_networks"] = [n["ssid"] for n in available_saved_networks]
                logger.info(f"Matched {len(available_saved_networks)} networks that are both saved and available")
                debug_info["debug_steps"].append(f"Final result: {len(available_saved_networks)} networks")
                
                # If we still don't have the current network, try to add it
                if current_ssid and not any(n["ssid"] == current_ssid for n in available_saved_networks):
                    logger.info(f"Current network {current_ssid} not in results, trying to add it")
                    debug_info["debug_steps"].append(f"Current network {current_ssid} not in results, trying to add it")
                    
                    # Add current network regardless of availability - if we're connected, it must be available
                    db_network = WiFiNetwork.objects.filter(ssid=current_ssid).first()
                    available_saved_networks.append({
                        'id': db_network.id if db_network else -1,
                        'ssid': current_ssid,
                        'isConnected': True,
                        'isSaved': True,
                        'isAvailable': True
                    })
                    debug_info["debug_steps"].append(f"Added current network {current_ssid} to results")
                
                # Sort networks: connected network first, then alphabetically
                available_saved_networks.sort(
                    key=lambda x: (not x['isConnected'], x['ssid'].lower())
                )
                
                # Final check - ensure current_ssid is properly set for networks
                if current_ssid:
                    # Loop through networks and update isConnected
                    for network_entry in available_saved_networks:
                        # Normalize for accurate comparison
                        if network_entry['ssid'].strip() == current_ssid.strip():
                            logger.info(f"Marking network as connected: {network_entry['ssid']}")
                            network_entry['isConnected'] = True
                            break
                
                # Return the list of networks along with debug info
                logger.info(f"Returning {len(available_saved_networks)} networks")
                
                # If there are no networks found, include debug info
                if len(available_saved_networks) == 0:
                    debug_info["debug_steps"].append("No networks found, returning debug info")
                    return JsonResponse({
                        'networks': [],
                        'debug_info': debug_info,
                        'message': 'No networks detected. See debug_info for details.'
                    })
                else:
                    return JsonResponse(available_saved_networks, safe=False)
                
            except Exception as e:
                error_msg = f"Error detecting networks: {str(e)}"
                logger.error(error_msg, exc_info=True)
                debug_info["error"] = str(e)
                debug_info["debug_steps"].append(error_msg)
                return JsonResponse({
                    'networks': [],
                    'debug_info': debug_info,
                    'error': error_msg
                })
        else:
            # Non-Windows platforms
            logger.warning(f"WiFi network detection not implemented for {platform.system()}")
            return JsonResponse([], safe=False)

    except Exception as e:
        logger.error(f"Error in get_available_saved_networks: {str(e)}", exc_info=True)
        return JsonResponse({
            'networks': [],
            'error': str(e)
        })

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

@require_http_methods(["GET"])
def test_wifi_detection(request):
    """Simple API endpoint to test WiFi detection using multiple methods"""
    try:
        import subprocess
        import platform
        import re
        
        debug_info = {
            'os': platform.system(),
            'methods': {}
        }
        
        # Method 1: WiFiConnectionManager
        try:
            from .tasks import WiFiConnectionManager
            manager = WiFiConnectionManager()
            current_ssid = manager.get_current_ssid()
            debug_info['methods']['wifi_manager'] = {
                'success': current_ssid is not None,
                'ssid': current_ssid
            }
        except Exception as e:
            debug_info['methods']['wifi_manager'] = {
                'success': False,
                'error': str(e)
            }
        
        # Method 2: Direct netsh command (Windows only)
        if platform.system() == 'Windows':
            try:
                result = subprocess.run(
                    ['netsh', 'wlan', 'show', 'interfaces'],
                    capture_output=True,
                    text=True,
                    check=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                # Save raw output
                debug_info['methods']['netsh_interfaces'] = {
                    'raw_output': result.stdout[:500],
                    'return_code': result.returncode
                }
                
                # Try to extract SSID
                match = re.search(r'SSID\s*:\s*(.*?)[\r\n]', result.stdout)
                if match:
                    debug_info['methods']['netsh_interfaces']['extracted_ssid'] = match.group(1).strip()
                    debug_info['methods']['netsh_interfaces']['success'] = True
                else:
                    debug_info['methods']['netsh_interfaces']['success'] = False
                    debug_info['methods']['netsh_interfaces']['reason'] = 'No SSID pattern match'
            except Exception as e:
                debug_info['methods']['netsh_interfaces'] = {
                    'success': False,
                    'error': str(e)
                }
                
        return JsonResponse(debug_info)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        })

@require_http_methods(["GET"])
def debug_current_wifi(request):
    """API endpoint to debug current WiFi detection"""
    try:
        import subprocess
        import platform
        import re

        debug_info = {
            "os": platform.system(),
            "methods_tried": []
        }

        # Method 1: Using WiFiConnectionManager
        try:
            from .tasks import WiFiConnectionManager
            manager = WiFiConnectionManager()
            current_ssid = manager.get_current_ssid()
            debug_info["method1"] = {
                "success": current_ssid is not None,
                "ssid": current_ssid
            }
            debug_info["methods_tried"].append("WiFiConnectionManager")
        except Exception as e:
            debug_info["method1"] = {
                "success": False,
                "error": str(e)
            }

        # Method 2: Direct netsh command
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ['netsh', 'wlan', 'show', 'interfaces'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                debug_info["method2"] = {
                    "raw_output": result.stdout[:500],
                    "output_type": type(result.stdout).__name__
                }
                
                # Try multiple regex patterns
                patterns = [
                    r'SSID\s*:\s*(.*?)[\r\n]',
                    r'SSID\s+:\s+(.*?)[\r\n]',
                    r'Profile\s*:\s*(.*?)[\r\n]'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, result.stdout)
                    if match and match.group(1).strip():
                        debug_info["method2"]["pattern"] = pattern
                        debug_info["method2"]["ssid"] = match.group(1).strip()
                        break
                
                debug_info["methods_tried"].append("netsh wlan show interfaces")
        except Exception as e:
            debug_info["method2"] = {
                "success": False,
                "error": str(e)
            }
        
        # Method 3: Try checking for state
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ['netsh', 'wlan', 'show', 'state'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                debug_info["method3"] = {
                    "raw_output": result.stdout[:500],
                    "output_type": type(result.stdout).__name__
                }
                
                match = re.search(r'SSID\s*:?\s*(.*?)[\r\n]', result.stdout)
                if match and match.group(1).strip():
                    debug_info["method3"]["ssid"] = match.group(1).strip()
                
                debug_info["methods_tried"].append("netsh wlan show state")
        except Exception as e:
            debug_info["method3"] = {
                "success": False,
                "error": str(e)
            }
                
        # Return all debug info
        return JsonResponse(debug_info)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        })

@require_http_methods(["GET"])
def get_connection_logs(request):
    """API endpoint to get the most recent connection logs"""
    try:
        # Get the 50 most recent logs
        logs = ConnectionLog.objects.order_by('-timestamp')[:50]
        
        # Convert to a list of dictionaries
        log_data = []
        for log in logs:
            log_data.append({
                'id': log.id,
                'timestamp': log.timestamp.isoformat(),
                'message': log.message,
                'is_success': log.is_success
            })
            
        return JsonResponse(log_data, safe=False)
    except Exception as e:
        logger.error(f"Error fetching connection logs: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': str(e)
        }, status=500)
