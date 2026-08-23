from rest_framework import serializers
from .models import *


class HomeAutomationSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeAutomation
        fields = "__all__"


class LocationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationLog
        fields = "__all__"