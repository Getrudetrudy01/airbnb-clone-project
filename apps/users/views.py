from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """Create a new guest or host account."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_scope = "auth"


class LoginView(TokenObtainPairView):
    """Exchange email + password for an access/refresh token pair."""

    throttle_scope = "auth"


class MeView(generics.RetrieveUpdateAPIView):
    """View or update the logged-in user's profile."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user
