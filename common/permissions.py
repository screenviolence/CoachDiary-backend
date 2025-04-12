from rest_framework import permissions


class IsTeacher(permissions.BasePermission):
    """
    Разрешение для предоставления доступа только учителям.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'role') and request.user.role == 'teacher'
