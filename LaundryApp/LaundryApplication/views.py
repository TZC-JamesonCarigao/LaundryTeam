from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from .models import LaundryData, DisplayData  # Import DisplayData here
import logging

#NEW Start
from .models import WiFiNetwork, Schedule, ConnectionLog
from .tasks import WiFiConnectionManager
#NEW End

import json
import subprocess
import platform
import re

# Configure logger  
logger = logging.getLogger(__name__)

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
        return render(request, self.template_name)

    def post(self, request):
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
        }, status=200)  # Send 200 status with error info for DataTables to display

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
        }, status=200)  # Send 200 status with error info for DataTables to display
    
#NEW Start
# @method_decorator(login_required, name='dispatch')
# class IndexView(View):
#     def get(self, request):
#         networks = WiFiNetwork.objects.filter(user=request.user)
#         schedules = Schedule.objects.filter(user=request.user)
#         current_ssid = WiFiConnectionManager().get_current_ssid()
        
#         context = {
#             'networks': networks,
#             'schedules': schedules,
#             'current_ssid': current_ssid,
#         }
#         return render(request, 'scheduler/settings.html', context)
    
#     def post(self, request):
#         if 'add_network' in request.POST:
#             ssid = request.POST.get('ssid')
#             password = request.POST.get('password')
#             is_primary = request.POST.get('is_primary') == 'on'
#             name = request.POST.get('name', ssid)
            
#             if WiFiNetwork.objects.filter(user=request.user, ssid=ssid).exists():
#                 messages.error(request, 'A network with this SSID already exists')
#             else:
#                 WiFiNetwork.objects.create(
#                     user=request.user,
#                     name=name,
#                     ssid=ssid,
#                     password=password,
#                     is_primary=is_primary
#                 )
#                 messages.success(request, 'Network added successfully')
        
#         elif 'add_schedule' in request.POST:
#             name = request.POST.get('name', 'New Schedule')
#             primary_id = request.POST.get('primary_network')
#             secondary_id = request.POST.get('secondary_network')
#             switch_time = request.POST.get('switch_time')
#             revert_time = request.POST.get('revert_time')
            
#             if switch_time == revert_time:
#                 messages.error(request, 'Switch and revert times cannot be the same')
#             else:
#                 Schedule.objects.create(
#                     user=request.user,
#                     name=name,
#                     primary_network_id=primary_id,
#                     secondary_network_id=secondary_id,
#                     switch_time=switch_time,
#                     revert_time=revert_time
#                 )
#                 messages.success(request, 'Schedule added successfully')
        
#         elif 'toggle_schedule' in request.POST:
#             schedule_id = request.POST.get('schedule_id')
#             schedule = Schedule.objects.get(id=schedule_id, user=request.user)
#             schedule.is_active = not schedule.is_active
#             schedule.save()
            
#             status = 'activated' if schedule.is_active else 'deactivated'
#             messages.success(request, f'Schedule {status} successfully')
        
#         elif 'delete_schedule' in request.POST:
#             schedule_id = request.POST.get('schedule_id')
#             Schedule.objects.filter(id=schedule_id, user=request.user).delete()
#             messages.success(request, 'Schedule deleted successfully')
        
#         elif 'delete_network' in request.POST:
#             network_id = request.POST.get('network_id')
#             WiFiNetwork.objects.filter(id=network_id, user=request.user).delete()
#             messages.success(request, 'Network deleted successfully')
        
#         return redirect('wifi_scheduler:settings')

# @method_decorator(login_required, name='dispatch')
# class StatusView(View):
    # def get(self, request):
    #     logs = ConnectionLog.objects.filter(user=request.user)[:50]
    #     current_ssid = WiFiConnectionManager().get_current_ssid()
        
    #     context = {
    #         'logs': logs,
    #         'current_ssid': current_ssid,
    #     }
    #     return render(request, 'scheduler/status.html', context)

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
        return JsonResponse({'error': str(e), 'detail': 'Error detecting WiFi networks'}, status=500)

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
def import_excel_data(request):
    """Import data from Excel file to the DisplayData table"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST requests allowed'})
    
    try:
        # Path to the Excel file
        excel_path = r"C:\Users\ADMIN\Documents\Dashboard.xlsx"
        
        # Check if file exists
        if not os.path.exists(excel_path):
            error_msg = f"Excel file not found at {excel_path}"
            ConnectionLog.objects.create(
                user=request.user,
                message=error_msg,
                is_success=False
            )
            return JsonResponse({'success': False, 'error': error_msg})
        
        # Load data from Excel
        try:
            df = pd.read_excel(excel_path)
        except Exception as e:
            error_msg = f"Error reading Excel file: {str(e)}"
            ConnectionLog.objects.create(
                user=request.user,
                message=error_msg,
                is_success=False
            )
            return JsonResponse({'success': False, 'error': error_msg})
        
        # Check for required columns
        expected_columns = [
            'DATE', 'Washing Machine', 'PROGRAM', 'TIME TO FILL', 'TOTAL TIME', 
            'ELEC', 'WATER 1', 'WATER 2', 'GAS', 'CHEMICAL', 'COST PER KW', 
            'GAS COST', 'Water cost', 'TOTAL'
        ]
        
        for col in expected_columns:
            if col not in df.columns:
                error_msg = f"Missing column in Excel: {col}"
                ConnectionLog.objects.create(
                    user=request.user,
                    message=error_msg,
                    is_success=False
                )
                return JsonResponse({'success': False, 'error': error_msg})
        
        # Get existing dates to avoid duplicates
        existing_dates = set(DisplayData.objects.values_list('date', flat=True))
        
        # Convert dates to strings for comparison
        existing_dates = {str(d) for d in existing_dates}
        
        # Start adding data
        records_added = 0
        records_skipped = 0
        
        for _, row in df.iterrows():
            # Convert date to string for comparison
            date_str = str(row['DATE'])
            
            # Skip if this date already exists
            if date_str in existing_dates:
                records_skipped += 1
                continue
            
            try:
                # Create a new DisplayData record
                display_data = DisplayData(
                    date=date_str,
                    washing_machine=row.get('Washing Machine', ''),
                    program=row.get('PROGRAM', ''),
                    time_to_fill=row.get('TIME TO FILL', None),
                    total_time=row.get('TOTAL TIME', None),
                    elec=row.get('ELEC', None),
                    water_1=row.get('WATER 1', None),
                    water_2=row.get('WATER 2', None),
                    gas=row.get('GAS', None),
                    chemical=row.get('CHEMICAL', None),
                    cost_per_kw=row.get('COST PER KW', None),
                    gas_cost=row.get('GAS COST', None),
                    water_cost=row.get('Water cost', None),
                    total=row.get('TOTAL', None)
                )
                display_data.save()
                records_added += 1
                
                # Add to existing dates to prevent duplicates
                existing_dates.add(date_str)
                
            except Exception as e:
                logger.error(f"Error importing row: {str(e)}", exc_info=True)
        
        # Log the result
        message = f"Imported {records_added} records from Excel ({records_skipped} skipped as duplicates)"
        ConnectionLog.objects.create(
            user=request.user,
            message=message,
            is_success=True
        )
        
        return JsonResponse({'success': True, 'message': message})
        
    except Exception as e:
        logger.error(f"Error in import_excel_data: {str(e)}", exc_info=True)
        error_msg = f"Error importing Excel data: {str(e)}"
        ConnectionLog.objects.create(
            user=request.user,
            message=error_msg,
            is_success=False
        )