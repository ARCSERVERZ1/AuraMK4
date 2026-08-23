"""
add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path , include
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(
    r"expense-category-plans",
    ExpenseCategoryPlanViewSet,
    basename="expense-category-plan"
)

urlpatterns = [
    # path('' , views.dem_dashboard),
    path('api/datalog/<int:count>/<str:user>/<str:date>', datalog_transaction_table),
    path('api/get_user_for_data_log/', get_user_for_data_log),
    path('api/classification_data/', txn_classification_data),
    path('', dashboard),
    path("api/", include(router.urls)),
    path('api/dummy-dashboard/', expense_dashboard, name='dummy-dashboard'),
    path('data_management', data_management),
    path("api/categories/", ExpenseCategoryListAPI.as_view()),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("api/transactions/", TransactionCreateView.as_view()),  # POST
    path("api/transactions/list/", TransactionListView.as_view()),  # GET (filtered)
    path("api/transactions/<int:uid>/", TransactionDetailView.as_view()),
    path("api/ai_analytics", ai_analytics),
    path( "api/bulk-update-transactions/",bulk_update_transactions),
    path("tester/", tester)
]