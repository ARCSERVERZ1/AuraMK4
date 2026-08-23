from rest_framework import serializers
from .models import MealLog


class MealLogCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealLog
        fields = "__all__"