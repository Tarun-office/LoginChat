from django.utils import timezone
from django.contrib.auth.models import User

class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Update last_active timestamp for authenticated users
        if request.user.is_authenticated:
            try:
                profile = request.user.profile
                profile.last_active = timezone.now()
                profile.save(update_fields=['last_active'])
            except:
                # Handle case where profile doesn't exist
                pass
        
        return response
