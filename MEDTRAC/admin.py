from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(MealTimeConfig)
admin.site.register(MealLog)
admin.site.register(MedicalProfile)
admin.site.register(MedicalEventLog)
admin.site.register(HealthAnalysisMeta)
admin.site.register(MealAnalysis)