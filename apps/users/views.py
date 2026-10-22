from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, serializers
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .demo import DEMO_LOGINS, DEMO_READ_ONLY_MESSAGE
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


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

    def perform_update(self, serializer):
        if self.request.user.is_demo:
            raise PermissionDenied(DEMO_READ_ONLY_MESSAGE)
        serializer.save()


class DemoLoginSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=list(DEMO_LOGINS))


def _demo_available():
    return settings.DEMO_LOGIN_ENABLED and User.objects.filter(email__in=DEMO_LOGINS.values()).exists()


class DemoLoginView(APIView):
    """One-click login as a shared demo account, for portfolio visitors.

    GET says whether demo login is available (demo data seeded and the feature enabled);
    POST {"role": "guest" | "host"} returns tokens for that account.
    """

    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    serializer_class = DemoLoginSerializer
    throttle_scope = "auth"

    def get_throttles(self):
        # Only logging in is rate-limited; the availability check runs on every page load.
        return super().get_throttles() if self.request.method == "POST" else []

    def get(self, request):
        return Response({"available": _demo_available()})

    def post(self, request):
        serializer = DemoLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not _demo_available():
            raise NotFound("Demo accounts aren't set up on this site.")
        user = User.objects.filter(email=DEMO_LOGINS[serializer.validated_data["role"]], is_active=True).first()
        if user is None:
            raise NotFound("That demo account isn't set up on this site.")
        refresh = RefreshToken.for_user(user)
        return Response({"refresh": str(refresh), "access": str(refresh.access_token)})
