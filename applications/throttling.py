from rest_framework.throttling import UserRateThrottle

class TestingUserRateThrottle(UserRateThrottle):
    """
    Custom throttle class for testing that doesn't rely on user.pk
    which might not be available in test mocks.
    """
    def get_cache_key(self, request, view):
        if not request.user:
            return None  # Only throttle authenticated requests
            
        # Use the user's str representation instead of pk for tests
        ident = str(request.user)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
