from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.decorators import login_required   
from . import views

urlpatterns = [
    # Main navigation routes
    path('', views.home, name='home'),  # Keep this as the root URL
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dosing-devices/', views.dosing_devices, name='dosing_devices'),
    path('classifications/', views.classifications, name='classifications'),
    path('products/', views.products, name='products'),
    path('report/', views.report, name='report'),
    path('settings/', views.settings, name='settings'),
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

]
