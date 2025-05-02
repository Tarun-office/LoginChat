from django.contrib import admin
from .models import OTP, UserProfile

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('email', 'otp', 'created_at')
    search_fields = ('email',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'get_full_name', 'profession', 'age')
    search_fields = ('username', 'user__first_name', 'user__last_name')
    list_filter = ('profession', 'age')
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'
