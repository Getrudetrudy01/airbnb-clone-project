from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import DemoLoginView, LoginView, MeView, RegisterView

app_name = "users"

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/demo/", DemoLoginView.as_view(), name="demo-login"),
    path("users/me/", MeView.as_view(), name="me"),
]
