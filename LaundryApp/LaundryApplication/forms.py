from django import forms
from .models import WiFiNetwork, Schedule

class WiFiNetworkForm(forms.ModelForm):
    class Meta:
        model = WiFiNetwork
        fields = ['name', 'ssid', 'password', 'is_primary']
        widgets = {
            'password': forms.PasswordInput(render_value=True)
        }

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['name', 'primary_network', 'secondary_network', 'switch_time', 'revert_time']
        
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['primary_network'].queryset = WiFiNetwork.objects.filter(user=user)
        self.fields['secondary_network'].queryset = WiFiNetwork.objects.filter(user=user)