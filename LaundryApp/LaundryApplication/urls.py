from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.decorators import login_required   
from . import views
from . import api_views
from .views import IndexView, StatusView
from .views import utility_costs

urlpatterns = [
    # Main navigation routes
    path('', views.home, name='home'),  # Keep this as the root URL
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dosing-devices/', views.dosing_devices, name='dosing_devices'),
    path('classifications/', views.classifications, name='classifications'),
    path('products/', views.products, name='products'),
    path('report/', views.report, name='report'),
    path('settings/', views.settings, name='settings'),  # Added a view for settings
    path('customers/', views.customers, name='customers'),
    path('users/', views.users, name='users'),
    path('downloads/', views.downloads, name='downloads'),
    path('meter-data/', views.meter_data, name='meter_data'),
    path('utility_costs/', views.utility_costs, name='utility_costs'),
    path('utility_costs/add/', views.utility_costs_add, name='utility_costs_add'),
    path('utility_costs/edit/<int:id>/', views.utility_costs_edit, name='utility_costs_edit'),
    path('utility_costs/delete/<int:id>/', views.utility_costs_delete, name='utility_costs_delete'),
    
    
    # Authentication routes
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('api/laundry-data/', login_required(views.laundry_data_ajax), name='laundry_data_ajax'),
    path('api/display-data/', login_required(views.display_data_ajax), name='display_data_ajax'),

    
    # Role-based views (kept for compatibility)
    path('admin/', views.admin_home, name='admin_home'),
    path('manager/', views.manager_home, name='manager_home'),
    path('operator/', views.operator_home, name='operator_home'),

    #NEW Start
    path('settings/', IndexView.as_view(), name='settings'),
    path('status/', StatusView.as_view(), name='status'),
    path('Status/', StatusView.as_view(), name='Status'),
    #NEW End

    # API endpoints for WiFi switching and Excel import
    path('api/saved-networks/', api_views.get_saved_networks, name='get_saved_networks'),
    path('api/available-saved-networks/', api_views.get_available_saved_networks, name='get_available_saved_networks'),
    path('api/switch-network/', views.switch_network, name='switch_network'),
    path('api/import-excel-data/', views.import_excel_data, name='import_excel_data'),

    # New meter data views
    path('api/meter-data-ajax/', views.meter_data_ajax, name='meter_data_ajax'),

    # New API endpoints
    path('api/import-excel/', views.import_excel_data, name='import_excel'),
    path('api/clear-meter-data/', views.clear_meter_data, name='clear_meter_data'),
    
    # WiFi Schedule API endpoints
    path('api/start-schedule/', api_views.start_schedule, name='start_schedule'),
    path('api/stop-schedule/', api_views.stop_schedule, name='stop_schedule'),
    path('api/schedule-status/', api_views.schedule_status, name='schedule_status'),
]
