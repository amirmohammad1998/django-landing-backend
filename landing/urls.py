from django.urls import path
from .views import RegisterPhoneView, LandingMediaView

app_name = "landing"
urlpatterns = [
    path("landing/", LandingMediaView.as_view(), name="landing_media"),
    path("register/", RegisterPhoneView.as_view(), name="register_phone"),
]

