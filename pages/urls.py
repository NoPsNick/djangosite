from django.urls import path, include
from django.contrib.auth.decorators import login_required
from rest_framework.routers import DefaultRouter

from .views import (
    AboutPageView,
    HomePageView,
    ProfilePageView,
    LegalInfos,
)

app_name = "pages"

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("sobre/", AboutPageView.as_view(), name="about"),

    path("perfil/<int:user_id>/", login_required(ProfilePageView.as_view()), name="profile"),

    # ToS URL
    path('tos/', LegalInfos.as_view(), name='termsofservice'),
]
