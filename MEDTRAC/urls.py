from django.contrib import admin
from django.urls import path , include
from .views import *

urlpatterns = [
    path('', mealdashboard_home),
    path('mealdata' , mealdata),
    path("api/meals/create/", MealLogBulkCreateAPI.as_view()),
    path("api/meals/list/", MealLogListAPI.as_view()),
    path("api/meals/update/<int:pk>/", MealLogUpdateAPI.as_view()),
    path("api/meals/delete/<int:pk>/", MealLogDeleteAPI.as_view()),
    path('api/ai-context/', get_ai_nutrition_context, name='ai_nutrition_context'),
    path('api/ai-context/save/',save_ai_analysis, name='save_ai_analysis'),
    path('api/tester/<str:parameter>/' , tester)
]