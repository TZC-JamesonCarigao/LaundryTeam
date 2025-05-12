from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.decorators import login_required   
from . import views
#from django.contrib.auth import views as auth_views #New
from .views import IndexView, StatusView #NEW

urlpatterns = [
    # Main navigation routes
    path('', views.home, name='home'),  # Keep this as the root URL
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dosing-devices/', views.dosing_devices, name='dosing_devices'),
    path('classifications/', views.classifications, name='classifications'),
    path('products/', views.products, name='products'),
    path('report/', views.report, name='report'),
    # path('settings/', views.settings, name='settings'),
    path('customers/', views.customers, name='customers'),
    path('users/', views.users, name='users'),
    path('downloads/', views.downloads, name='downloads'),
    
    # Authentication routes
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('api/laundry-data/', login_required(views.laundry_data_ajax), name='laundry_data_ajax'),
    path('api/display-data/', login_required(views.display_data_ajax), name='display_data_ajax'),

    
    # Role-based views (kept for compatibility)
    path('admin/', views.admin_home, name='admin_home'),
    path('manager/', views.manager_home, name='manager_home'),
    path('operator/', views.operator_home, name='operator_home'),
    # path('', include('scheduler.urls')),

    #NEW Start
    path('settings/', IndexView.as_view(), name='settings'),
    path('status/', StatusView.as_view(), name='status'),
    #NEW End

    # API endpoints for WiFi switching and Excel import
    path('api/saved-networks/', views.get_saved_networks, name='get_saved_networks'),
    path('api/switch-network/', views.switch_network, name='switch_network'),
    path('api/import-excel-data/', views.import_excel_data, name='import_excel_data'),
]
