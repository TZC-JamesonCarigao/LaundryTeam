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
        from .tasks import WiFiConnectionManager
        manager = WiFiConnectionManager()
        
        # Get current SSID
        current_ssid = manager.get_current_ssid()
        
        # Get all saved networks from the database
        networks = WiFiNetwork.objects.all()
        
        # Format the response
        network_list = []
        for network in networks:
            network_list.append({
                'id': network.id,
                'ssid': network.ssid,
                'isConnected': network.ssid == current_ssid,
                'isSaved': True,
                'isAvailable': True  # Assuming all networks in DB are available
            })
            
        return JsonResponse(network_list, safe=False)
    except Exception as e:
        logger.error(f"Error fetching networks: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)

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
