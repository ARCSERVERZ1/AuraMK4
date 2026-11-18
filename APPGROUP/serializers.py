from rest_framework import serializers
from .models import *


class DeviceTelemetrySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceTelemetry
        fields = '__all__'
        read_only_fields = ['logged_at']

class HomeAutomationSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeAutomation
        fields = "__all__"


class LocationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationLog
        fields = "__all__"