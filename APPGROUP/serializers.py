from rest_framework import serializers
from .models import *


class DeviceTelemetrySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceTelemetry
        fields = '__all__'
        read_only_fields = ['logged_at']

    def to_internal_value(self, data):
        print("RAW INCOMING DATA:", dict(data))
        print("RAW REMARKS KEYS:", {k: data.get(k) for k in data if "remark" in k.lower()})

        mutable_data = data.copy() if hasattr(data, "copy") else dict(data)
        if "remarks" in mutable_data and "Remarks" not in mutable_data:
            mutable_data["Remarks"] = mutable_data["remarks"]

        validated = super().to_internal_value(mutable_data)
        print("VALIDATED REMARKS:", validated.get("Remarks"))
        return validated

    def perform_create(self, serializer):
        print("ABOUT TO SAVE NEW RECORD:", serializer.validated_data)
        serializer.save()

class HomeAutomationSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeAutomation
        fields = "__all__"


class LocationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationLog
        fields = "__all__"