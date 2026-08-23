from django.shortcuts import render
from .serializers import *
from rest_framework.decorators import api_view, permission_classes
from .models import *
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
import json
from collections import defaultdict
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.http import JsonResponse
from django.db.models import Sum
from datetime import datetime, timedelta

# Create your views here.

@api_view(['POST'])
def datalog_transaction_table(request, count, user, date):

        table_data = transactions_data_Serializer(data=request.data)

        if table_data.is_valid():
            if count == 1:
                Transaction.objects.filter(user=user, date=date).exclude(payment_method='Manual_Entry').delete()
            table_data.save()
            return Response(table_data.data, status=201)
        return Response(table_data.errors, status=400)

@api_view(['GET'])
def get_user_for_data_log(request):
    print(f"request for get_user_for_data_log {request.data}")

    User = get_user_model()
    emails = User.objects.values_list('username','email' ,'imap_password','payment_methods').filter(auto_data_log=True)
    return Response(list(emails)  , status=200)

def dashboard(request):

    context = {
        "user": request.user.username,
        "mode":3
    }
    return render(request, 'DEM_Dashboard.html' , context = context)

def data_management(request):
    # Fetch active categories

    return render(request, "DEM_DataManagement.html", {
        'user': request.user.username,
        'mode':3# ✅ correct structure
    })

@api_view(['GET'])
def txn_classification_data(request):
    user = request.GET.get("user")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    print(user , start_date, end_date)

    qs = (
        Transaction.objects
        .filter(
            user=user,
            date__range=[start_date, end_date],
            is_auto_cat=1
        )
        .values(
            "receiver_bank",
            "category",
            "sub_category"
        )
        .distinct()
        .order_by("receiver_bank", "category", "sub_category")
    )
    data = list(qs)  # or serialize properly if needed
    grouped_data = defaultdict(list)

    for item in data:
        grouped_data[item["receiver_bank"]].append(
            (item["category"], item["sub_category"])
        )
    return JsonResponse(grouped_data, safe=False)

class TransactionListView(APIView):
    """
    GET /api/transactions/?user=Sanjay&start_date=2025-01-01&end_date=2025-01-31
    """

    def get(self, request):
        user = request.query_params.get("user")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        # -------------------------
        # Mandatory validation
        # -------------------------
        if not user or not start_date or not end_date:
            return Response(
                {
                    "error": "user, start_date and end_date are mandatory"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        start = parse_date(start_date)
        end = parse_date(end_date)

        if not start or not end:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )

        qs = Transaction.objects.filter(
            user=user,
            date__range=[start, end]
        ).order_by("-date")

        # print(qs)

        serializer = transactions_data_Serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TransactionCreateView(APIView):
    """
    POST /api/transactions/
    """

    def post(self, request):
        serializer = transactions_data_Serializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class TransactionDetailView(APIView):
    """
    GET    /api/transactions/<uid>/
    PUT    /api/transactions/<uid>/
    DELETE /api/transactions/<uid>/
    """

    def get_object(self, uid):
        return get_object_or_404(Transaction, uid=uid)

    # READ SINGLE
    def get(self, request, uid):
        transaction = self.get_object(uid)
        serializer = transactions_data_Serializer(transaction)
        return Response(serializer.data)

    # UPDATE
    def put(self, request, uid):
        transaction = self.get_object(uid)
        serializer = transactions_data_Serializer(
            transaction,
            data=request.data,
            partial=True  # allow partial update
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    # DELETE
    def delete(self, request, uid):
        transaction = self.get_object(uid)
        transaction.delete()
        return Response(
            {"message": "Transaction deleted"},
            status=status.HTTP_204_NO_CONTENT
        )

class ExpenseCategoryListAPI(APIView):
    """
    Returns all ACTIVE categories grouped by category
    """

    def get(self, request):
        qs = ExpenseCategory.objects.filter(status="ACTIVE")

        data = {}
        for obj in qs:
            data.setdefault(obj.category, []).append({
                "id": obj.id,
                "sub_category": obj.sub_category,
                "notes": obj.notes
            })

        return Response({
            "status": "success",
            "categories": data
        })




class ExpenseCategoryPlanViewSet(viewsets.ModelViewSet):
    """
    CREATE, READ, UPDATE, DELETE API
    """
    queryset = ExpenseCategoryPlan.objects.all()
    serializer_class = ExpenseCategoryPlanSerializer

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter
    ]

    filterset_fields = ["user", "month", "category"]
    search_fields = ["category"]
    ordering_fields = ["planned_amount", "category", "month"]
    ordering = ["category"]

    def create(self, request, *args, **kwargs):
        """
        Override create to handle unique constraint nicely
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_create(serializer)
        except Exception as e:
            return Response(
                {"error": "Plan already exists for this user, month and category"},
                status=status.HTTP_400_BAD_REQUEST
            )

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

# views.py
from django.http import JsonResponse
from datetime import datetime
from django.db.models.functions import TruncMonth

def expense_dashboard(request):


    print(request.GET)
    user = request.GET.get('user')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # DEM/views.py


    """
    Return budget summary for a user between start_date and end_date (inclusive)
    Aggregate per category (no duplicates)
    """
    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    # 1️⃣ Get unique categories
    categories = list(ExpenseCategory.objects.order_by().values_list('category', flat=True).distinct())
    # 2️⃣ Planned budgets per category


    plans = (
        ExpenseCategoryPlan.objects
        .filter(user= user)
        .annotate(month_only=TruncMonth('month'))
        .filter(
            month_only__gte=start_date.replace(day=1),
            month_only__lte=end_date.replace(day=1)
        ).exclude(category='Non-Countable')
        .values('category')
        .annotate(planned=Sum('planned_amount'))
    )

    plan_map = {p['category']: float(p['planned']) for p in plans}

    print(plan_map)

    # 3️⃣ Spent amounts per category
    txns = Transaction.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date
    ).exclude(category='Non-Countable').values('category').annotate(spent=Sum('amount'))

    spent_map = {t['category']: float(t['spent']) for t in txns}
    print(spent_map)
    # 4️⃣ Prepare chart data (one entry per category)
    planned_data = [plan_map.get(cat, 0) for cat in categories]
    spent_data = [spent_map.get(cat, 0) for cat in categories]

    total_budget = sum(planned_data)
    total_spent = sum(spent_data)
    available_budget = total_budget - total_spent

    # 5️⃣ Daily spend line chart
    day_count = (end_date - start_date).days + 1
    daily_labels = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(day_count)]

    daily_txns = Transaction.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date
    ).values('date').annotate(total=Sum('amount'))

    daily_map = {d['date'].strftime("%Y-%m-%d"): float(d['total']) for d in daily_txns}
    daily_data = [daily_map.get(day, 0) for day in daily_labels]

    payload = {
        "totalBudget": total_budget,
        "totalSpent": total_spent,
        "availableBudget": available_budget,
        "budgetChart": {
            "labels": categories,
            "datasets": [
                {"label": "Planned", "data": planned_data},
                {"label": "Spent", "data": spent_data},
            ]
        },
        "donutChart": {
            "labels": categories,
            "datasets": [{"data": spent_data}]
        },
        "lineChart": {
            "labels": daily_labels,
            "datasets": [{"label": "Daily Spend", "data": daily_data}]
        }
    }

    return JsonResponse(payload)

def tester(request):
    user = request.user

    context = {
        "username": user.username,
        "house_name": user.family_name,
        "email": user.email,
    }
    return JsonResponse (context , safe=False)

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from .models import Transaction


@api_view(['POST'])
def ai_analytics(request):
    User = get_user_model()

    user_param = request.data.get('user', '').strip()
    start_date = request.data.get('start_date', '').strip()
    end_date = request.data.get('end_date', '').strip()

    # Validate required fields
    if not user_param or not start_date or not end_date:
        return Response(
            {"error": "user, start_date and end_date are mandatory"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user_obj = User.objects.get(username=user_param)
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    daily_txns = (
        Transaction.objects
        .filter(
            user=user_param,
            date__range=[start_date, end_date],
            sub_category__iexact='Unclassified',
            status='1'
        )
        .values('uid','timestamp', 'amount' , 'receiver_bank' , 'category', 'sub_category')
    )

    response = {
        "category": list(ExpenseCategory.objects.filter( status = 'ACTIVE').values( 'category' , 'sub_category' , 'notes')),
        "Txns" : list(daily_txns)
    }


    return Response(response, status=status.HTTP_200_OK)


from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
import traceback


@csrf_exempt
def bulk_update_transactions(request):

    if request.method != "POST":
        return JsonResponse(
            {"error": "POST only"},
            status=405
        )

    try:
        # =========================
        # PARSE REQUEST
        # =========================
        data = json.loads(request.body.decode("utf-8"))

        if isinstance(data, dict):
            data = [data]

        # =========================
        # EXTRACT UIDs
        # =========================
        uids = [
            item.get("uid")
            for item in data
            if item.get("uid") is not None
        ]

        if not uids:
            return JsonResponse(
                {"error": "No valid UIDs found"},
                status=400
            )

        # =========================
        # FETCH FROM DB
        # =========================
        qs = Transaction.objects.filter(uid__in=uids)

        transactions_map = {
            obj.uid: obj for obj in qs
        }

        # =========================
        # BUILD UPDATE LIST
        # =========================
        update_objects = []

        for item in data:

            uid = item.get("uid")
            obj = transactions_map.get(uid)

            if not obj:
                continue

            obj.category = item.get("category", obj.category)
            obj.sub_category = item.get("sub_category", obj.sub_category)
            obj.status = item.get("status", obj.status)

            update_objects.append(obj)

        # =========================
        # BULK UPDATE
        # =========================
        if update_objects:

            with transaction.atomic():
                Transaction.objects.bulk_update(
                    update_objects,
                    ["category", "sub_category", "status"],
                    batch_size=1000
                )

        return JsonResponse({
            "success": True,
            "received": len(data),
            "updated": len(update_objects)
        })

    except Exception as e:

        traceback.print_exc()

        return JsonResponse(
            {"error": str(e)},
            status=500
        )