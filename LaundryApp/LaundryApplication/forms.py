from django import forms
from .models import WiFiNetwork, Schedule, UtilityCost

class WiFiNetworkForm(forms.ModelForm):
    """Form for WiFi networks"""
    class Meta:
        model = WiFiNetwork
        fields = ['ssid', 'password', 'is_primary']
        widgets = {
            'password': forms.PasswordInput(render_value=True),
            'is_primary': forms.CheckboxInput(),
        }

class ScheduleForm(forms.ModelForm):
    """Form for WiFi switching schedules"""
    class Meta:
        model = Schedule
        fields = ['primary_network', 'secondary_network', 'switch_time', 'revert_time']
        widgets = {
            'switch_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'revert_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # No user filtering needed since we don't have a user field
        self.fields['primary_network'].queryset = WiFiNetwork.objects.all()
        self.fields['secondary_network'].queryset = WiFiNetwork.objects.all()

class UtilityCostForm(forms.ModelForm):
    """Form for updating utility costs"""
    class Meta:
        model = UtilityCost
        fields = ['electricity_cost', 'gas_cost', 'water_cost', 'effective_date']
        widgets = {
            'electricity_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'gas_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'water_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'effective_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'electricity_cost': 'Electricity Cost (per unit)',
            'gas_cost': 'Gas Cost (per unit)',
            'water_cost': 'Water Cost (per unit)',
        }

# class UtilityCostForm(forms.ModelForm):
#     electricity_cost = forms.DecimalField(
#         label='Electricity Cost (per unit)',
#         widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
#     )
#     gas_cost = forms.DecimalField(
#         label='Gas Cost (per unit)',
#         widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
#     )
#     water_cost = forms.DecimalField(
#         label='Water Cost (per unit)',
#         widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
#     )

#     class Meta:
#         model = UtilityCost
#         fields = ['electricity_cost', 'gas_cost', 'water_cost']