from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
# from django.contrib.auth.models import User #New
from django.utils import timezone #NEW


# Authentication models - actively used
class Profile(models.Model):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Manager', 'Manager'),
        ('Operator', 'Operator'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Operator')

    def __str__(self):
        return f'{self.user.username} - {self.role}'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class LaundryData(models.Model):
    id = models.AutoField(primary_key=True)
    batchid = models.CharField(max_length=50, db_index=True, db_column='batchid') 
    time = models.CharField(max_length=100, db_index=True, db_column='Time')  
    duration = models.CharField(max_length=50, db_column='Duration')
    alarms = models.TextField(null=True, blank=True, db_column='Alarms')
    machine = models.CharField(max_length=100, null=True, blank=True, db_column='Machine')
    classification = models.CharField(max_length=100, null=True, blank=True, db_column='Classification')
    triggers = models.TextField(null=True, blank=True, db_column='Triggers')
    device = models.CharField(max_length=100, null=True, blank=True, db_column='Device')
    abpcost = models.CharField(max_length=50, null=True, blank=True, db_column='abpcost')
    dosagecost = models.CharField(max_length=50, null=True, blank=True, db_column='dosagecost')
    weight = models.CharField(max_length=50, null=True, blank=True, db_column='Weight')
    dosings = models.CharField(max_length=10, null=True, blank=True, db_column='Dosings')
    ph = models.CharField(max_length=50, null=True, blank=True, db_column='pH') 
    tempdis = models.CharField(max_length=50, null=True, blank=True, db_column='tempdis') 
    temprange = models.CharField(max_length=50, null=True, blank=True, db_column='temprange')
    customer = models.CharField(max_length=100, null=True, blank=True, db_column='Customer')  

    class Meta:
        db_table = 'LaundryData'  
        managed = True
        indexes = [
            models.Index(fields=['batchid']),
            models.Index(fields=['time']),
            models.Index(fields=['customer']),
        ]

    def __str__(self):
        return f"Batch {self.batchid} - {self.customer}"

    @property
    def abpcost_as_float(self):
        """Return abpcost as float if possible, otherwise None"""
        try:
            return float(self.abpcost) if self.abpcost else None
        except (ValueError, TypeError):
            return None

    @property
    def dosagecost_as_float(self):
        """Return dosagecost as float if possible, otherwise None"""
        try:
            return float(self.dosagecost) if self.dosagecost else None
        except (ValueError, TypeError):
            return None

    @property
    def weight_as_float(self):
        """Return weight as float if possible, otherwise None"""
        try:
            return float(self.weight) if self.weight else None
        except (ValueError, TypeError):
            return None

    @property
    def dosings_as_bool(self):
        """Return dosings as boolean if possible, otherwise None"""
        if self.dosings is None:
            return None
        return self.dosings.lower() == 'true'

class DisplayData(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.CharField(max_length=50, db_index=True, db_column='DATE')
    washing_machine = models.CharField(max_length=100, db_index=True, db_column='Washing Machine')
    program = models.FloatField(null=True, blank=True, db_column='PROGRAM')
    time_to_fill = models.FloatField(null=True, blank=True, db_column='TIME TO FILL')
    total_time = models.FloatField(null=True, blank=True, db_column='TOTAL TIME')
    elec = models.FloatField(null=True, blank=True, db_column='ELEC')
    water_1 = models.FloatField(null=True, blank=True, db_column='WATER 1')
    water_2 = models.FloatField(null=True, blank=True, db_column='WATER 2')
    gas = models.FloatField(null=True, blank=True, db_column='GAS')
    chemical = models.FloatField(null=True, blank=True, db_column='CHEMICAL')
    cost_per_kw = models.FloatField(null=True, blank=True, db_column='COST PER KW')
    gas_cost = models.FloatField(null=True, blank=True, db_column='GAS COST')
    water_cost = models.FloatField(null=True, blank=True, db_column='Water cost')
    total = models.FloatField(null=True, blank=True, db_column='TOTAL')

    class Meta:
        db_table = 'DisplayData'
        managed = True
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['washing_machine']),
        ]

    def __str__(self):
        return f"DisplayData {self.date} - {self.washing_machine}"

    @property
    def program_as_float(self):
        """Return program as float if possible, otherwise None"""
        try:
            return float(self.program) if self.program is not None else None
        except (ValueError, TypeError):
            return None

    @property
    def total_as_float(self):
        """Return total as float if possible, otherwise None"""
        try:
            return float(self.total) if self.total is not None else None
        except (ValueError, TypeError):
            return None

# class WiFiNetwork(models.Model): #New
#     name = models.CharField(max_length=100)
#     ssid = models.CharField(max_length=100)
#     password = models.CharField(max_length=100, blank=True, null=True)
#     is_primary = models.BooleanField(default=False)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)

#     def __str__(self):
#         return f"{self.name} ({self.ssid})"

# class Schedule(models.Model): #New
#     name = models.CharField(max_length=100)
#     primary_network = models.ForeignKey(
#         WiFiNetwork, 
#         related_name='primary_schedules',
#         on_delete=models.CASCADE
#     )
#     secondary_network = models.ForeignKey(
#         WiFiNetwork, 
#         related_name='secondary_schedules',
#         on_delete=models.CASCADE
#     )
#     switch_time = models.TimeField()
#     revert_time = models.TimeField()
#     is_active = models.BooleanField(default=False)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.name} (Active: {self.is_active})"

#NEW Start
# class WiFiNetwork(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     name = models.CharField(max_length=100)
#     ssid = models.CharField(max_length=100)
#     password = models.CharField(max_length=100, blank=True, null=True)
#     is_primary = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.name} ({self.ssid})"

# class Schedule(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     name = models.CharField(max_length=100)
#     primary_network = models.ForeignKey(
#         WiFiNetwork, 
#         related_name='primary_schedules',
#         on_delete=models.CASCADE
#     )
#     secondary_network = models.ForeignKey(
#         WiFiNetwork, 
#         related_name='secondary_schedules',
#         on_delete=models.CASCADE
#     )
#     switch_time = models.TimeField()
#     revert_time = models.TimeField()
#     is_active = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.name} (Active: {self.is_active})"


#---2nd----

# class WiFiNetwork(models.Model):
#     ssid = models.CharField(max_length=100, unique=True)
#     password = models.CharField(max_length=100, blank=True, null=True)
#     is_primary = models.BooleanField(default=False)
    
#     def __str__(self):
#         return self.ssid

# class Schedule(models.Model):
#     primary_network = models.ForeignKey(WiFiNetwork, on_delete=models.CASCADE, related_name='primary_schedules')
#     secondary_network = models.ForeignKey(WiFiNetwork, on_delete=models.CASCADE, related_name='secondary_schedules')
#     switch_time = models.TimeField()
#     revert_time = models.TimeField()
#     is_active = models.BooleanField(default=False)
#     last_switch = models.DateTimeField(null=True, blank=True)
    
#     def __str__(self):
#         return f"Schedule {self.id}"

# class ConnectionLog(models.Model):
#     timestamp = models.DateTimeField(auto_now_add=True)
#     message = models.TextField()
#     is_success = models.BooleanField(default=False)
    
#     class Meta:
#         ordering = ['-timestamp']
    
#     def __str__(self):
#         return f"{self.timestamp}: {self.message[:50]}"

#---2nd---
# class WiFiNetwork(models.Model):
#     ssid = models.CharField(max_length=100, unique=True)
#     password = models.CharField(max_length=100, blank=True, null=True)
#     is_primary = models.BooleanField(default=False)
    
#     def __str__(self):
#         return self.ssid

# class Schedule(models.Model):
#     primary_network = models.ForeignKey(WiFiNetwork, on_delete=models.CASCADE, related_name='primary_schedules')
#     secondary_network = models.ForeignKey(WiFiNetwork, on_delete=models.CASCADE, related_name='secondary_schedules')
#     switch_time = models.TimeField()
#     revert_time = models.TimeField()
#     is_active = models.BooleanField(default=False)
#     last_switch = models.DateTimeField(null=True, blank=True)
    
#     def __str__(self):
#         return f"Schedule {self.id}"

# class ConnectionLog(models.Model):
#     timestamp = models.DateTimeField(auto_now_add=True)
#     message = models.TextField()
#     is_success = models.BooleanField(default=False)
    
#     class Meta:
#         ordering = ['-timestamp']
    
#     def __str__(self):
#         return f"{self.timestamp}: {self.message[:50]}"

class WiFiNetwork(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ssid = models.CharField(max_length=100)
    password = models.CharField(max_length=100, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.ssid

class Schedule(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    primary_network = models.ForeignKey(WiFiNetwork, related_name='primary_schedules', on_delete=models.CASCADE)
    secondary_network = models.ForeignKey(WiFiNetwork, related_name='secondary_schedules', on_delete=models.CASCADE)
    switch_time = models.TimeField()
    revert_time = models.TimeField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Schedule {self.id}"

class ConnectionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    is_success = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp}: {self.message[:50]}"
#NEW End