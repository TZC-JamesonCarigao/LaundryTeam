from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile #BatchLog
from .models import WiFiNetwork, Schedule, ConnectionLog #NEW


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    list_select_related = ('profile',)

    def get_role(self, instance):
        return instance.profile.role
    get_role.short_description = 'Role'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

#NEW Start
@admin.register(WiFiNetwork)
class WiFiNetworkAdmin(admin.ModelAdmin):
    list_display = ('ssid', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('ssid',)

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('id', 'primary_network', 'secondary_network', 'switch_time', 'revert_time', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('primary_network__ssid', 'secondary_network__ssid')

@admin.register(ConnectionLog)
class ConnectionLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'message', 'is_success')
    list_filter = ('is_success',)
    search_fields = ('message',)
    readonly_fields = ('timestamp',)
#NEW End
