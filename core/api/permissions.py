from rest_framework import permissions


class IsLiderOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_superuser or request.user.groups.filter(name='Lideres').exists()
