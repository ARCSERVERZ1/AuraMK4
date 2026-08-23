# serializers.py
from rest_framework import serializers
from .models import *


class transactions_data_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'  # You can also specify specific fields instead of '__all__'

class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = [
            "id",
            "category",
            "sub_category",
            "notes",
            "status"
        ]
from rest_framework import serializers
from .models import ExpenseCategoryPlan


class ExpenseCategoryPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategoryPlan
        fields = [
            "id",
            "user",
            "month",
            "category",
            "planned_amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_month(self, value):
        """
        Enforce YYYY-MM-01 (first day of month only)
        """
        # if value.day != 1:
        #     raise serializers.ValidationError(
        #         "Month must be the first day of the month (YYYY-MM-01)."
        #     )
        return value
