from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    message = "You can only modify your own reviews."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author_id == request.user.id
