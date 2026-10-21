from rest_framework import permissions


class IsHostOrReadOnly(permissions.BasePermission):
    """Anyone can read; only users with the host role can create listings."""

    message = "Only hosts can create listings."

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_host


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Only the listing's host can change or delete it."""

    message = "You can only modify your own listings."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.host_id == request.user.id
