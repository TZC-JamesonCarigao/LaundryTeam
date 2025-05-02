from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import LaundryData, DisplayData  # Import DisplayData here
import logging

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

@login_required
def settings(request):
    return blank_page(request, "Settings")

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