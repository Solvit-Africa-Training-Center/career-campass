from rest_framework import permissions

class HasRolePermission(permissions.BasePermission):
    """
    Custom permission to grant access based on user roles.
    Usage: set `required_roles` attribute in your view.
    """

    def has_permission(self, request, view):
        required_roles = getattr(view, 'required_roles', [])

        if not request.user or not request.user.is_authenticated:
            return False

        user_roles = request.user.roles.values_list('code', flat=True)

        # Check if user has at least one of the required roles
        return any(role in user_roles for role in required_roles)
