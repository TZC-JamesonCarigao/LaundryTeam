from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from .models import LaundryData, DisplayData, MeterData  # Import MeterData here
import logging
from .models import UtilityCost
from .forms import UtilityCostForm

#NEW Start
from .models import WiFiNetwork, Schedule, ConnectionLog
from .tasks import WiFiConnectionManager, meter_data_fetcher  # Import meter_data_fetcher here
#NEW End

import json
import subprocess
import platform
import re
import os

# Configure logger  
logger = logging.getLogger(__name__)

def detect_wifi_robust(allowed_networks=None):
    """
    Robust WiFi detection function specifically for login page
    Uses multiple detection methods with fallbacks
    """
    # Default allowed networks if not specified
    if allowed_networks is None:
        allowed_networks = ['Converge_2.4GHz_Yj3u']
    
    current_ssid = None
    debug_info = []
    
    # Try multiple methods to detect WiFi
    os_name = platform.system()
    
    # Method 1: Using WiFiConnectionManager (existing method)
    try:
        wifi_manager = WiFiConnectionManager()
        current_ssid = wifi_manager.get_current_ssid()
        debug_info.append(f"Method 1 result: {current_ssid}")
    except Exception as e:
        debug_info.append(f"Method 1 error: {str(e)}")
    
    # Method 2: Direct command execution with alternative parsing
    if not current_ssid and os_name == "Windows":
        try:
            # Use more explicit encoding parameters
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'interfaces'],
                capture_output=True, 
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # More flexible regex patterns
            patterns = [
                r'SSID\s*:\s*(.*?)[\r\n]',
                r'SSID\s+:\s+(.*?)[\r\n]',
                r'Profile\s*:\s*(.*?)[\r\n]',
                r'Profile\s+:\s+(.*?)[\r\n]'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, result.stdout)
                if match and match.group(1).strip():
                    current_ssid = match.group(1).strip()
                    debug_info.append(f"Method 2 pattern '{pattern}' matched: {current_ssid}")
                    break
            
            if not current_ssid:
                debug_info.append(f"Method 2: No regex matches. Command output: {result.stdout[:200]}...")
        except Exception as e:
            debug_info.append(f"Method 2 error: {str(e)}")
    
    # Method 3: Try alternative commands for Windows
    if not current_ssid and os_name == "Windows":
        try:
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'state'],
                capture_output=True, 
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # Look for SSID in output
            match = re.search(r'SSID\s*:?\s*(.*?)[\r\n]', result.stdout)
            if match and match.group(1).strip():
                current_ssid = match.group(1).strip()
                debug_info.append(f"Method 3 result: {current_ssid}")
            else:
                debug_info.append(f"Method 3: Command ran but no SSID found")
        except Exception as e:
            debug_info.append(f"Method 3 error: {str(e)}")
    
    # Log debug info
    logger.debug("WiFi detection debug info: " + " | ".join(debug_info))
    
    # Determine if WiFi is allowed
    is_allowed_wifi = False
    if current_ssid:
        # Exact match
        if current_ssid in allowed_networks:
            is_allowed_wifi = True
        else:
            # Partial match check (for potential encoding issues)
            for network in allowed_networks:
                if network in current_ssid or current_ssid in network:
                    logger.info(f"Partial WiFi match: '{current_ssid}' matches allowed network '{network}'")
                    current_ssid = network  # Use the known network name
                    is_allowed_wifi = True
                    break
    
    return {
        'current_ssid': current_ssid,
        'is_allowed_wifi': is_allowed_wifi,
        'allowed_networks': allowed_networks,
        'debug_info': debug_info
    }

class CustomLoginView(View):
    template_name = 'login.html'  

    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return redirect('/admin/')
            elif hasattr(request.user, 'profile'):
                if request.user.profile.role == 'Manager':
                    return redirect('dashboard')  # Updated: was 'manager_home'
                elif request.user.profile.role == 'Operator':
                    return redirect('dashboard')  # Updated: was 'operator_home'
            return redirect('home')
        
        # Use the robust WiFi detection function
        wifi_info = detect_wifi_robust()
        
        # Debug logging
        logger.info(f"Login page - Detected WiFi: {wifi_info['current_ssid']}")
        logger.debug(f"WiFi detection info: {wifi_info['debug_info']}")
        
        # Extract info for template context
        current_ssid = wifi_info['current_ssid']
        is_allowed_wifi = wifi_info['is_allowed_wifi']
        allowed_networks = wifi_info['allowed_networks']
        
        context = {
            'current_ssid': current_ssid,
            'is_allowed_wifi': is_allowed_wifi,
            'allowed_networks': allowed_networks,
            'detecting': False,  # WiFi detection completed
        }
        return render(request, self.template_name, context)

    def post(self, request):
        # Check WiFi again on form submission as an additional security measure
        wifi_info = detect_wifi_robust()
        current_ssid = wifi_info['current_ssid']
        is_allowed_wifi = wifi_info['is_allowed_wifi']
        allowed_networks = wifi_info['allowed_networks']
        
        if not is_allowed_wifi:
            messages.error(request, 'Login not allowed from this network.')
            return render(request, self.template_name, {
                'current_ssid': current_ssid,
                'is_allowed_wifi': is_allowed_wifi,
                'allowed_networks': allowed_networks
            })
        
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome, {username}!')
            if user.is_superuser:
                return redirect('/admin/')
            elif hasattr(user, 'profile'):
                if user.profile.role == 'Manager':
                    return redirect('dashboard')  # Updated: was 'manager_home'
                elif user.profile.role == 'Operator':
                    return redirect('dashboard')  # Updated: was 'operator_home'
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
        return render(request, self.template_name)

# Role-Based Home Views
@login_required
def admin_home(request):
    return blank_page(request, "Admin Home")



@login_required
def manager_home(request):
    return blank_page(request, "Manager Home")



@login_required
def operator_home(request):
    return blank_page(request, "Operator Home")


@login_required
def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')

# Blank page view for most pages
def blank_page(request, title=None):
    return render(request, 'blank.html', {'title': title})

@login_required
def home(request):
    """Home page dashboard"""
    return render(request, 'dashboard.html', {'title': 'Dashboard'})


@login_required
def dosing_devices(request):
    return blank_page(request, "Dosing Devices")

@login_required
def classifications(request):
    return blank_page(request, "Classifications")

@login_required
def products(request):
    return blank_page(request, "Products")

@login_required
def report(request):
    """View for displaying all LaundryData records in a report."""
    return render(request, 'report.html', {'title': 'Laundry Data Report'})

# @login_required
# def settings(request):
#     return blank_page(request, "Settings")

@login_required
def customers(request):
    return blank_page(request, "Customers")

@login_required
def users(request):
    return blank_page(request, "Users")

@login_required
def downloads(request):
    """View for displaying all DisplayData records."""
    return render(request, 'downloads.html', {'title': 'Downloads Data'})

@login_required
def display_data_ajax(request):
    try:
        # Get all records from DisplayData table
        queryset = DisplayData.objects.all()
        
        # If specific export request, return all data
        if request.GET.get('export') == 'true' or request.GET.get('get_all'):
            # Return all data without filtering
            queryset = DisplayData.objects.all().order_by('id')
        else:
            # Apply date filtering if provided
            from_date = request.GET.get('fromDate')
            to_date = request.GET.get('toDate')
            
            if from_date:
                queryset = queryset.filter(date__gte=from_date)
            if to_date:
                queryset = queryset.filter(date__lte=to_date)
        
        # Prepare response data
        data = []
        for item in queryset:
            data.append({
                "id": item.id,
                "date": item.date or "",
                "washing_machine": item.washing_machine or "",
                "program": item.program or "",
                "time_to_fill": item.time_to_fill or "",
                "total_time": item.total_time or "",
                "elec": item.elec or "",
                "water_1": item.water_1 or "",
                "water_2": item.water_2 or "",
                "gas": item.gas or "",
                "chemical": item.chemical or "",
                "cost_per_kw": item.cost_per_kw or "",
                "gas_cost": item.gas_cost or "",
                "water_cost": item.water_cost or "",
                "total": item.total or ""
            })
        
        # Return data in the format expected by DataTables
        return JsonResponse({
            "draw": int(request.GET.get('draw', 1)),
            "recordsTotal": queryset.count(),
            "recordsFiltered": queryset.count(),
            "data": data
        })

    except Exception as e:
        # Log detailed error information
        logger.error(f"Error in display_data_ajax: {str(e)}", exc_info=True)
        
        # Return a properly formatted error response for DataTables
        return JsonResponse({
            "draw": int(request.GET.get('draw', 1)),
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        }, status=200, Status=200)  # Send 200 status with error info for DataTables to display

# @login_required
# def dashboard(request):
#     networks = WiFiNetwork.objects.filter(user=request.user) #New
#     schedules = Schedule.objects.filter(user=request.user)
#     recent_switches = SwitchLog.objects.filter(
#         schedule__user=request.user
#     ).order_by('-created_at')[:10]
    
#     return render(request, 'scheduler/dashboard.html', {
#         'networks': networks,
#         'schedules': schedules,
#         'recent_switches': recent_switches
#     }
#     return render(request, 'dashboard.html', {'title': 'Dashboard'}))
    

# @login_required #New
# def add_network(request):
#     if request.method == 'POST':
#         form = WiFiNetworkForm(request.POST)
#         if form.is_valid():
#             network = form.save(commit=False)
#             network.user = request.user
#             network.save()
#             messages.success(request, 'WiFi network added successfully!')
#             return redirect('dashboard')
#     else:
#         form = WiFiNetworkForm()
#     return render(request, 'scheduler/add_network.html', {'form': form})

# @login_required #New
# def create_schedule(request):
#     if request.method == 'POST':
#         form = ScheduleForm(request.user, request.POST)
#         if form.is_valid():
#             schedule = form.save(commit=False)
#             schedule.user = request.user
#             schedule.save()
#             messages.success(request, 'Schedule created successfully!')
#             return redirect('dashboard')
#     else:
#         form = ScheduleForm(request.user)
#     return render(request, 'scheduler/create_schedule.html', {'form': form})

# @login_required #New
# def toggle_schedule(request, schedule_id):
#     schedule = Schedule.objects.get(id=schedule_id, user=request.user)
#     schedule.is_active = not schedule.is_active
#     schedule.save()
#     status = "activated" if schedule.is_active else "deactivated"
#     messages.success(request, f'Schedule {status} successfully!')
#     return redirect('dashboard')

@login_required
def dashboard(request):
    return render(request, 'dashboard.html', {'title': 'Dashboard'})

# Update home view to redirect to dashboard
@login_required
def home(request):
    return redirect('dashboard')

@login_required
def laundry_data_ajax(request):
    try:
        # Get customers for filter dropdown if requested
        if request.GET.get('get_customers'):
            customers = LaundryData.objects.exclude(customer__isnull=True)\
                                        .exclude(customer__exact='')\
                                        .order_by('customer')\
                                        .values_list('customer', flat=True)\
                                        .distinct()
            return JsonResponse({'customers': list(customers)})
        
        # If specific export request, return all data
        if request.GET.get('export') == 'true' or request.GET.get('get_all'):
            # Return all data without filtering
            queryset = LaundryData.objects.all().order_by('id')
        else:
            # Simply get all records from LaundryData table
            queryset = LaundryData.objects.all()
            
            # Apply date filtering if provided
            from_date = request.GET.get('fromDate')
            to_date = request.GET.get('toDate')
            customer_filter = request.GET.get('customer')
            
            if from_date:
                queryset = queryset.filter(time__gte=from_date)
            if to_date:
                queryset = queryset.filter(time__lte=to_date)
            if customer_filter:
                queryset = queryset.filter(customer=customer_filter)
        
        # Prepare response data
        data = []
        for item in queryset:
            # Handle potential None values to prevent serialization issues
            # Use correct field names exactly as defined in the model
            data.append({
                "id": item.id,
                "batchid": item.batchid or "",
                "time": item.time or "",
                "duration": item.duration or "",
                "alarms": item.alarms or "",
                "machine": item.machine or "",
                "classification": item.classification or "",
                "triggers": item.triggers or "",
                "device": item.device or "",
                "abpcost": item.abpcost or "",
                "dosagecost": item.dosagecost or "",
                "weight": item.weight or "",
                "dosings": item.dosings or "",
                "ph": item.ph or "",
                "tempdis": item.tempdis or "",  
                "temprange": item.temprange or "",
                "customer": item.customer or ""
            })
        
        # Return all data in the format expected by DataTables
        return JsonResponse({
            "draw": int(request.GET.get('draw', 1)),  # Echo back the draw parameter
            "recordsTotal": queryset.count(),         # Total records before filtering
            "recordsFiltered": queryset.count(),      # Total records after filtering (same here as we don't filter)
            "data": data
        })

    except Exception as e:
        # Log detailed error information
        logger.error(f"Error in laundry_data_ajax: {str(e)}", exc_info=True)
        
        # Return a properly formatted error response for DataTables
        return JsonResponse({
            "draw": int(request.GET.get('draw', 1)),
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        }, status=200, Status=200)  # Send 200 status with error info for DataTables to display
    
#---2nd---
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages

# Apply login_required to all methods of the class
@method_decorator(login_required, name='dispatch')
class IndexView(View):
    def get(self, request):
        networks = WiFiNetwork.objects.all()
        schedules = Schedule.objects.all()
        current_ssid = WiFiConnectionManager().get_current_ssid()
        
        context = {
            'networks': networks,
            'schedules': schedules,
            'current_ssid': current_ssid,
        }
        return render(request, 'settings.html', context)
    
    def post(self, request):
        if 'add_network' in request.POST:
            ssid = request.POST.get('ssid')
            password = request.POST.get('password')
            is_primary = request.POST.get('is_primary') == 'on'
            
            if WiFiNetwork.objects.filter(ssid=ssid).exists():
                messages.error(request, 'A network with this SSID already exists')
            else:
                WiFiNetwork.objects.create(
                    ssid=ssid,
                    password=password,
                    is_primary=is_primary
                )
                messages.success(request, 'Network added successfully')
        
        elif 'add_schedule' in request.POST:
            primary_id = request.POST.get('primary_network')
            secondary_id = request.POST.get('secondary_network')
            switch_time = request.POST.get('switch_time')
            revert_time = request.POST.get('revert_time')
            
            if switch_time == revert_time:
                messages.error(request, 'Switch and revert times cannot be the same')
            else:
                Schedule.objects.create(
                    primary_network_id=primary_id,
                    secondary_network_id=secondary_id,
                    switch_time=switch_time,
                    revert_time=revert_time
                )
                messages.success(request, 'Schedule added successfully')
        
        elif 'toggle_schedule' in request.POST:
            schedule_id = request.POST.get('schedule_id')
            schedule = Schedule.objects.get(id=schedule_id)
            schedule.is_active = not schedule.is_active
            schedule.save()
            
            status = 'activated' if schedule.is_active else 'deactivated'
            messages.success(request, f'Schedule {status} successfully')

            Status = 'activated' if schedule.is_active else 'deactivated'
            messages.success(request, f'Schedule {Status} successfully')
        
        return redirect('settings')
    
@method_decorator(login_required, name='dispatch')
class StatusView(View):
    def get(self, request):
        logs = ConnectionLog.objects.all()[:50]
        current_ssid = WiFiConnectionManager().get_current_ssid()
        
        context = {
            'logs': logs,
            'current_ssid': current_ssid,
        }
        return render(request, 'status.html', context)
        return render(request, 'Status.html', context)

@login_required
def get_saved_networks(request):
    """API endpoint to retrieve saved and available WiFi networks from the system"""
    try:
        available_networks = []
        current_ssid = None
        
        # Get operating system
        os_name = platform.system()
        
        # For debugging
        debug_info = {
            "os": os_name,
            "current_ssid": None,
            "saved_networks": [],
            "available_networks": [],
            "matched_networks": []
        }
        
        if os_name == "Windows":
            # Get current connection
            current_process = subprocess.run(
                ['netsh', 'wlan', 'show', 'interfaces'], 
                capture_output=True, 
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            current_output = current_process.stdout
            
            # Extract current SSID
            current_match = re.search(r'SSID\s+:\s+(.+)\n', current_output)
            if current_match:
                current_ssid = current_match.group(1).strip()
                debug_info["current_ssid"] = current_ssid

            # Get list of all networks
            saved_process = subprocess.run(
                ['netsh', 'wlan', 'show', 'profiles'], 
                capture_output=True, 
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            saved_output = saved_process.stdout
            
            # Extract saved network names (using a more flexible regex)
            saved_networks = re.findall(r'All User Profile\s+:\s+(.+)(?:\r|\n)', saved_output)
            debug_info["saved_networks"] = saved_networks
            
            # Get available networks
            available_process = subprocess.run(
                ['netsh', 'wlan', 'show', 'networks'], 
                capture_output=True, 
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            available_output = available_process.stdout
            
            # Extract available SSIDs (more flexible regex)
            available_ssids = re.findall(r'SSID \d+ : (.+)(?:\r|\n)', available_output)
            debug_info["available_networks"] = available_ssids
            
            # Create a normalized list for better matching
            normalized_available = [ssid.strip().lower() for ssid in available_ssids]
            
            # Find networks that are both saved and available using case-insensitive matching
            for ssid in saved_networks:
                normalized_ssid = ssid.strip().lower()
                if normalized_ssid in normalized_available:
                    network = {
                        'ssid': ssid.strip(),
                        'isConnected': ssid.strip() == current_ssid,
                        'isSaved': True,
                        'isAvailable': True
                    }
                    available_networks.append(network)
                    debug_info["matched_networks"].append(ssid.strip())
            
        # ... the macOS and Linux code stays the same ...
            
        # If no networks found using automatic detection, create dummy data for testing
        if len(available_networks) == 0:
            logger.warning("No networks found using automatic detection. Check system commands or network adapter.")
            # Optional: Return debug info along with empty list
            return JsonResponse({
                "networks": [],
                "debug_info": debug_info,
                "error": "No networks detected. Check network adapter or permissions."
            })
        
        return JsonResponse(available_networks, safe=False)
        
    except Exception as e:
        logger.error(f"Error in get_saved_networks: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e), 'detail': 'Error detecting WiFi networks'}, status=500, Status=500)

import datetime
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

# ...existing code...

@login_required
def switch_network(request):
    """API endpoint to switch the computer's WiFi network"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST requests allowed'})
    
    try:
        data = json.loads(request.body)
        ssid = data.get('ssid')
        is_secondary = data.get('isSecondary', False)
        
        if not ssid:
            return JsonResponse({'success': False, 'error': 'SSID is required'})
        
        # Get operating system
        os_name = platform.system()
        success = False
        error_msg = ""
        
        if os_name == "Windows":
            try:
                # Connect to the specified WiFi network
                connect_process = subprocess.run(
                    ['netsh', 'wlan', 'connect', 'name=' + ssid],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                if connect_process.returncode == 0:
                    success = True
                    message = f"Successfully connected to {ssid}"
                else:
                    error_msg = connect_process.stderr or "Failed to connect to network"
            except Exception as e:
                error_msg = str(e)
                
        elif os_name == "Darwin":  # macOS
            try:
                # Connect to the specified WiFi network on macOS
                connect_process = subprocess.run(
                    ['networksetup', '-setairportnetwork', 'en0', ssid],
                    capture_output=True,
                    text=True
                )
                
                if connect_process.returncode == 0:
                    success = True
                    message = f"Successfully connected to {ssid}"
                else:
                    error_msg = connect_process.stderr or "Failed to connect to network"
            except Exception as e:
                error_msg = str(e)
        
        else:  # Linux or other OS
            error_msg = f"Network switching not implemented for {os_name}"
        
        # Log the connection attempt
        if success:
            ConnectionLog.objects.create(
                user=request.user,
                message=f"Switched to {ssid}",
                is_success=True
            )
            return JsonResponse({'success': True, 'message': f"Successfully connected to {ssid}"})
        else:
            ConnectionLog.objects.create(
                user=request.user,
                message=f"Failed to switch to {ssid}: {error_msg}",
                is_success=False
            )
            return JsonResponse({'success': False, 'error': error_msg})
            
    except Exception as e:
        logger.error(f"Error in switch_network: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def meter_data(request):
    """View for displaying MeterData records"""
    # Count records for debugging
    record_count = MeterData.objects.count()
    logger.info(f"MeterData records available: {record_count}")
    
    return render(request, 'meter_data.html', {'title': 'Meter Data'})

@login_required
def meter_data_ajax(request):
    """API endpoint to retrieve meter data for DataTables"""
    try:
        # Get pagination parameters from DataTables
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 25))
        
        # Check if this is an auto-refresh request
        is_auto_refresh = 'autoRefresh' in request.GET
        
        # Get total record count
        total_records = MeterData.objects.count()
        
        # Start with base queryset ordered by timestamp (newest first)
        queryset = MeterData.objects.all().order_by('-timestamp')
        
        # Apply filters only if they are explicitly provided
        from_date = request.GET.get('fromDate', '').strip()
        to_date = request.GET.get('toDate', '').strip()
        meter_id = request.GET.get('meterId', '').strip()
        
        # Only apply filters if they have values and this is not an auto-refresh
        if not is_auto_refresh:
            if from_date:
                queryset = queryset.filter(timestamp__gte=from_date)
            if to_date:
                queryset = queryset.filter(timestamp__lte=to_date)
            if meter_id:
                queryset = queryset.filter(meterId=meter_id)
        
        # Get filtered count
        filtered_records = queryset.count()
        
        # Apply pagination
        paginated_queryset = queryset[start:start + length]
        
        # Prepare response data
        data = []
        for item in paginated_queryset:
            data.append({
                "id": item.id,
                "meterId": item.meterId,
                "consumptionRecordId": item.consumptionRecordId or "",  # Handle None values
                "timestamp": item.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                "value": item.value,
                "correctionFactor": item.correctionFactor,
                "created_at": item.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        logger.debug(f"Returning {len(data)} meter records (page {start//length + 1}, size {length})")
        
        # Return data in the format expected by DataTables
        return JsonResponse({
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": data
        })
    
    except Exception as e:
        logger.error(f"Error in meter_data_ajax: {str(e)}", exc_info=True)
        return JsonResponse({
            "draw": int(request.GET.get('draw', 1)),
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        }, status=200, Status=200)

@login_required
def clear_meter_data(request):
    """Admin function to clear all meter data records"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to perform this action")
        return redirect('dashboard')
        
    if request.method == 'POST' and request.POST.get('confirm') == 'yes':
        from django.db import connection
        
        # Get record count before deletion
        count = MeterData.objects.count()
        
        # Use raw SQL for faster deletion
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM LaundryApplication_meterdata")
            
        messages.success(request, f"Successfully deleted {count} meter data records")
        return redirect('dashboard')
    
    return render(request, 'clear_data_confirm.html')

@login_required
def utility_costs(request):
    # Get the most recent utility costs if they exist
    latest_costs = UtilityCost.objects.last()
    
    if request.method == 'POST':
        form = UtilityCostForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Utility costs saved successfully!')
            return redirect('utility_costs')
    else:
        form = UtilityCostForm(instance=latest_costs)
    
    context = {
        'form': form,
        'latest_costs': latest_costs,
    }
    return render(request, 'utility_costs.html', context)

@login_required
def settings(request):
    """View for the WiFi schedule settings page"""
    # Get the current WiFi connection
    from .tasks import WiFiConnectionManager
    current_ssid = WiFiConnectionManager().get_current_ssid()
    
    # Get the most recent log entries
    logs = ConnectionLog.objects.all().order_by('-timestamp')[:20]
    
    context = {
        'title': 'WiFi Schedule Settings',
        'current_ssid': current_ssid,
        'logs': logs
    }
    
    return render(request, 'settings.html', context)

# Add these new views for utility costs CRUD operations

@login_required
def utility_costs(request):
    utility_costs = UtilityCost.objects.all().order_by('-effective_date')
    
    context = {
        'title': 'Utility Costs',
        'utility_costs': utility_costs,
    }
    return render(request, 'utility_costs.html', context)

@login_required
def utility_costs_add(request):
    if request.method == 'POST':
        form = UtilityCostForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Utility cost added successfully!')
        else:
            messages.error(request, 'Error adding utility cost: ' + str(form.errors))
    
    return redirect('utility_costs')

@login_required
def utility_costs_edit(request, id):
    if request.method == 'POST':
        instance = get_object_or_404(UtilityCost, id=id)
        form = UtilityCostForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Utility cost updated successfully!')
        else:
            messages.error(request, 'Error updating utility cost: ' + str(form.errors))
    
    return redirect('utility_costs')

@login_required
def utility_costs_delete(request, id):
    if request.method == 'POST':
        instance = get_object_or_404(UtilityCost, id=id)
        instance.delete()
        messages.success(request, 'Utility cost deleted successfully!')
    
    return redirect('utility_costs')