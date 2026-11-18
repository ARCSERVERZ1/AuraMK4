from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

home_router = DefaultRouter()
location_router = DefaultRouter()
home_router.register(r'api', HomeAutomationViewSet, basename='home-automation')
location_router.register(r'api', LocationLogViewSet, basename='location')

telemetry_router = DefaultRouter()
telemetry_router.register(r'api', DeviceTelemetryViewSet, basename='telemetry')
#
# urlpatterns = [
#     # This automatically includes all CRUD routes:
#     # GET /api/telemetry/ (List)
#     # POST /api/telemetry/ (Create)
#     # GET /api/telemetry/<id>/ (Retrieve)
#     # PUT/PATCH /api/telemetry/<id>/ (Update)
#     # DELETE /api/telemetry/<id>/ (Destroy)
#
# ]

urlpatterns = [
    path('home-auto-view/', include(home_router.urls)),
    path('location/', include(location_router.urls)),
    path('home-auto', home_auto_dashboard),
    path('jarvis', jarvis),
    path('home-auto-action/', trigger_home_auto_action),
    path('location-homepage', location_log_dashboard),
    path('telemetry/', include(telemetry_router.urls)),
]