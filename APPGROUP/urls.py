from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

home_router = DefaultRouter()
location_router = DefaultRouter()
home_router.register(r'api', HomeAutomationViewSet, basename='home-automation')
location_router.register(r'api', LocationLogViewSet, basename='location')
urlpatterns = [
    path('home-auto-view/', include(home_router.urls)),
    path('location/', include(location_router.urls)),
    path('home-auto', home_auto_dashboard),
    path('home-auto-action/', trigger_home_auto_action),
    path('location-homepage', location_log_dashboard),
]