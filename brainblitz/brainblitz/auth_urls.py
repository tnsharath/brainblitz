from django.contrib.auth import views as auth_views
from django.urls import path

from . import auth_views as local_views

urlpatterns = [
    path("signup/", local_views.signup, name="signup"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("profile/", local_views.profile, name="profile"),
]

