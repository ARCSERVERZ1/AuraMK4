from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import MealLogCreateSerializer
from django.db.models import Sum

class MealLogBulkCreateAPI(APIView):

    def post(self, request):
        meals = request.data.get("meals", [])

        if not meals:
            return Response(
                {"error": "No meals provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        saved_data = []

        for meal in meals:
            serializer = MealLogCreateSerializer(data=meal)
            if serializer.is_valid():
                instance = serializer.save()
                saved_data.append(serializer.data)
            else:
                return Response(serializer.errors, status=400)

        return Response(
            {
                "message": "Meals saved successfully",
                "data": saved_data
            },
            status=status.HTTP_201_CREATED
        )

# =====================================================
# LIST API (Filter by User + Date Range)
# =====================================================

class MealLogListAPI(APIView):

    def get(self, request):

        user = request.GET.get("user")
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        queryset = MealLog.objects.all()

        # Filter user
        if user:
            queryset = queryset.filter(user=user)

        # Filter date range
        if start_date and end_date:
            queryset = queryset.filter(
                timestamp__date__gte=start_date,
                timestamp__date__lte=end_date
            )

        serializer = MealLogCreateSerializer(queryset, many=True)
        return Response(serializer.data)


# =====================================================
# UPDATE API (Edit ALL Columns)
# =====================================================

class MealLogUpdateAPI(APIView):

    def put(self, request, pk):
        print("Updating:", pk)
        print("Incoming:", request.data)

        try:
            meal = MealLog.objects.get(uid=pk)
        except MealLog.DoesNotExist:
            return Response({"error": "Meal not found"}, status=404)

        data = request.data.copy()

        # Convert empty strings to None for float fields
        float_fields = [
            "quantity",
            "estimated_calories",
            "estimated_protein",
            "estimated_carbs",
            "estimated_fats",
            "estimated_fiber",
            "estimated_sugar",
            "estimated_sodium",
        ]

        for field in float_fields:
            if data.get(field) == "":
                data[field] = None

        serializer = MealLogCreateSerializer(
            meal,
            data=data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        print("Errors:", serializer.errors)
        return Response(serializer.errors, status=400)

        return Response(serializer.errors, status=400)


# =====================================================
# DELETE API
# =====================================================

class MealLogDeleteAPI(APIView):

    def delete(self, request, pk):

        try:
            meal = MealLog.objects.get(uid=pk)
        except MealLog.DoesNotExist:
            return Response({"error": "Meal not found"}, status=404)

        meal.delete()
        return Response({"message": "Meal deleted successfully"})


from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Sum
from datetime import date, datetime, timedelta
from collections import defaultdict
from .models import MealLog

from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Sum
from datetime import date, datetime, timedelta
from collections import defaultdict
from .models import MealLog


from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Sum
from datetime import date, datetime, timedelta
from collections import defaultdict
from .models import MealLog


def get_hour_float(dt):
    if not dt:
        return None
    return dt.hour + (dt.minute / 60.0)

def is_fasting(log):
    """Helper to consistently identify if a meal log is a skipped/fasting meal."""
    return log.quantity == 0 or (log.food_name and "fasting" in log.food_name.lower())

# def mealdashboard_home(request):
#     user = request.user
#     selected_username = request.GET.get("user", user.username)
#     family_name = user.family_name
#     User = get_user_model()
#     usernames = User.objects.filter(family_name=family_name).values_list("username", flat=True)
#     print(user, selected_username, user.family_name)
#
#     # Date configurations
#     today = timezone.localtime(timezone.now()).date()
#     first_day_of_month = today.replace(day=1)
#
#     start_date_str = request.GET.get("start_date")
#     end_date_str = request.GET.get("end_date")
#
#     if start_date_str and end_date_str:
#         try:
#             start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
#             end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
#         except ValueError:
#             start_date = first_day_of_month
#             end_date = today
#     else:
#         start_date = first_day_of_month
#         end_date = today
#
#     logs = MealLog.objects.filter(
#         user=selected_username,
#         timestamp__date__gte=start_date,
#         timestamp__date__lte=end_date
#     ).order_by('timestamp')
#
#     delta_days = (end_date - start_date).days + 1
#     daily_dates = [start_date + timedelta(days=i) for i in range(delta_days)]
#     logs_by_date = defaultdict(list)
#
#     times_fasting = 0
#     for log in logs:
#         logs_by_date[log.timestamp.date()].append(log)
#         if is_fasting(log):
#             times_fasting += 1
#
#     # Streak Logic:
#     # Because fasting meals are logged as actual records, they will naturally
#     # satisfy the len() > 0 check and keep the streak alive.
#     streak = 0
#     check_date = end_date - timedelta(days=1)
#     while check_date >= start_date:
#         if check_date in logs_by_date and len(logs_by_date[check_date]) > 0:
#             streak += 1
#             check_date -= timedelta(days=1)
#         else:
#             break
#
#     def init_metric_set():
#         return {
#             "all": {"cal": 0, "p": 0, "c": 0, "f": 0, "fib": 0},
#             "breakfast": {"cal": 0, "p": 0, "c": 0, "f": 0, "fib": 0},
#             "lunch": {"cal": 0, "p": 0, "c": 0, "f": 0, "fib": 0},
#             "dinner": {"cal": 0, "p": 0, "c": 0, "f": 0, "fib": 0}
#         }
#
#     daily_buckets = defaultdict(init_metric_set)
#     weekly_buckets = defaultdict(init_metric_set)
#     monthly_buckets = defaultdict(init_metric_set)
#
#     high_res_labels = []
#     tb_daily, tl_daily, td_daily = [], [], []
#     qb_daily, ql_daily, qd_daily = [], [], []
#
#     food_b_daily, food_l_daily, food_d_daily = [], [], []
#
#     for d in daily_dates:
#         day_str = d.strftime("%b %d")
#         high_res_labels.append(day_str)
#         week_key = f"Week {d.isocalendar()[1]}"
#         month_key = d.strftime("%b %Y")
#
#         day_logs = logs_by_date[d]
#
#         # Group logs by meal type
#         b_logs = [l for l in day_logs if l.meal_type and "breakfast" in l.meal_type.lower()]
#         l_logs = [l for l in day_logs if l.meal_type and "lunch" in l.meal_type.lower()]
#         d_logs = [l for l in day_logs if l.meal_type and "dinner" in l.meal_type.lower()]
#
#         # Filter out fasting logs exclusively for the Time Pattern chart calculation
#         b_logs_time = [l for l in b_logs if not is_fasting(l)]
#         l_logs_time = [l for l in l_logs if not is_fasting(l)]
#         d_logs_time = [l for l in d_logs if not is_fasting(l)]
#
#         # Time Pattern: Averages based only on actual food consumed (ignoring fasting)
#         tb_daily.append(round(sum(get_hour_float(l.timestamp) for l in b_logs_time) / len(b_logs_time), 1) if b_logs_time else None)
#         tl_daily.append(round(sum(get_hour_float(l.timestamp) for l in l_logs_time) / len(l_logs_time), 1) if l_logs_time else None)
#         td_daily.append(round(sum(get_hour_float(l.timestamp) for l in d_logs_time) / len(d_logs_time), 1) if d_logs_time else None)
#
#         # Quantity Pattern: Fasting logs will naturally contribute 0 to the sum here
#         qb_daily.append(sum(l.quantity or 0 for l in b_logs))
#         ql_daily.append(sum(l.quantity or 0 for l in l_logs))
#         qd_daily.append(sum(l.quantity or 0 for l in d_logs))
#
#         # Include "Fasting" in the tooltip item strings so users see it in the UI
#         food_b_daily.append(", ".join([l.food_name for l in b_logs if l.food_name]) or "Not logged")
#         food_l_daily.append(", ".join([l.food_name for l in l_logs if l.food_name]) or "Not logged")
#         food_d_daily.append(", ".join([l.food_name for l in d_logs if l.food_name]) or "Not logged")
#
#         # Macros & Calories: Since fasting values are 0, they safely do not inflate the totals
#         for log in day_logs:
#             cals = log.estimated_calories or 0
#             p = log.estimated_protein or 0
#             c = log.estimated_carbs or 0
#             f = log.estimated_fats or 0
#             fib = log.estimated_fiber or 0
#             m_type = log.meal_type.lower() if log.meal_type else "unknown"
#
#             for bucket, key in [(daily_buckets, day_str), (weekly_buckets, week_key), (monthly_buckets, month_key)]:
#                 for target_group in ["all", m_type]:
#                     if target_group in bucket[key]:
#                         bucket[key][target_group]["cal"] += cals
#                         bucket[key][target_group]["p"] += p
#                         bucket[key][target_group]["c"] += c
#                         bucket[key][target_group]["f"] += f
#                         bucket[key][target_group]["fib"] += fib
#
#     def package_timeframe_data(timeframe_bucket):
#         labels = list(timeframe_bucket.keys())
#         output = {
#             "labels": labels,
#             "high_res_labels": high_res_labels,
#             "time_breakfast": tb_daily, "time_lunch": tl_daily, "time_dinner": td_daily,
#             "qty_breakfast": qb_daily, "qty_lunch": ql_daily, "qty_dinner": qd_daily,
#             "food_breakfast": food_b_daily, "food_lunch": food_l_daily, "food_dinner": food_d_daily
#         }
#
#         for group in ["all", "breakfast", "lunch", "dinner"]:
#             output[f"calorie_{group}"] = [round(timeframe_bucket[lbl][group]["cal"]) for lbl in labels]
#
#             tot_p = sum(timeframe_bucket[lbl][group]["p"] for lbl in labels)
#             tot_c = sum(timeframe_bucket[lbl][group]["c"] for lbl in labels)
#             tot_f = sum(timeframe_bucket[lbl][group]["f"] for lbl in labels)
#             tot_fib = sum(timeframe_bucket[lbl][group]["fib"] for lbl in labels)
#             output[f"macro_{group}"] = [round(tot_p), round(tot_c), round(tot_f), round(tot_fib)]
#
#         return output
#
#     # Overall Average Calories Calculation
#     range_total_cals = sum(sum(l.estimated_calories or 0 for l in logs_by_date[d]) for d in daily_dates)
#     avg_cals = round(range_total_cals / delta_days) if delta_days > 0 else 0
#
#     yesterday = today - timedelta(days=1)
#     yesterday_cals = MealLog.objects.filter(user=selected_username, timestamp__date=yesterday).aggregate(
#         total=Sum('estimated_calories'))['total'] or 0
#
#     context = {
#         "current_user": selected_username,
#         "selected_username": selected_username,
#         "users": usernames,
#         "start_date": start_date.strftime("%Y-%m-%d"),
#         "end_date": end_date.strftime("%Y-%m-%d"),
#         "dashboard": {
#             "avg_calories": avg_cals,
#             "kpi": {
#                 "calories_yesterday": round(yesterday_cals),
#                 "target_calories": 2100,
#                 "times_fasting": times_fasting,
#                 "meals_logged_actual": logs.count(),
#                 "meals_logged_expected": delta_days * 3,
#                 "streak": streak
#             },
#             "health_score": 78,
#             "health_flags": ["Low fiber intake across segments"],
#             "ai_summary": ["Consistent macro configurations monitored"],
#             "charts": {
#                 "daily": package_timeframe_data(daily_buckets),
#                 "weekly": package_timeframe_data(weekly_buckets),
#                 "monthly": package_timeframe_data(monthly_buckets)
#             }
#         }
#     }
#     return render(request, "MEDTRAC_Home.html", context)


from django.shortcuts import render
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict
from django.contrib.auth import get_user_model
from django.db.models import Sum

# Make sure to import your new models!
from .models import MealLog, HealthAnalysisMeta, MealAnalysis


# Note: Assuming is_fasting and get_hour_float are defined elsewhere in your file
# from .utils import is_fasting, get_hour_float

def mealdashboard_home(request):
    user = request.user
    selected_username = request.GET.get("user", user.username)
    family_name = user.family_name
    User = get_user_model()
    usernames = User.objects.filter(family_name=family_name).values_list("username", flat=True)
    print(user, selected_username, user.family_name)

    # Date configurations
    today = timezone.localtime(timezone.now()).date()
    first_day_of_month = today.replace(day=1)

    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            start_date = first_day_of_month
            end_date = today
    else:
        start_date = first_day_of_month
        end_date = today

    logs = MealLog.objects.filter(
        user=selected_username,
        timestamp__date__gte=start_date,
        timestamp__date__lte=end_date
    ).order_by('timestamp')

    delta_days = (end_date - start_date).days + 1
    daily_dates = [start_date + timedelta(days=i) for i in range(delta_days)]
    logs_by_date = defaultdict(list)

    times_fasting = 0
    for log in logs:
        logs_by_date[log.timestamp.date()].append(log)
        if is_fasting(log):
            times_fasting += 1

    # Streak Logic
    streak = 0
    check_date = end_date - timedelta(days=1)
    while check_date >= start_date:
        if check_date in logs_by_date and len(logs_by_date[check_date]) > 0:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    def init_metric_set():
        return {
            "all": {"cal": 0, "p": 0, "c": 0, "f": 0, "fib": 0},
            "breakfast": {"cal": 0, "p": 0, "c": 0, "f": 0, "fib": 0},
            "lunch": {"cal": 0, "p": 0, "c": 0, "f": 0, "fib": 0},
            "dinner": {"cal": 0, "p": 0, "c": 0, "f": 0, "fib": 0}
        }

    daily_buckets = defaultdict(init_metric_set)
    weekly_buckets = defaultdict(init_metric_set)
    monthly_buckets = defaultdict(init_metric_set)

    high_res_labels = []
    tb_daily, tl_daily, td_daily = [], [], []
    qb_daily, ql_daily, qd_daily = [], [], []

    food_b_daily, food_l_daily, food_d_daily = [], [], []

    for d in daily_dates:
        day_str = d.strftime("%b %d")
        high_res_labels.append(day_str)
        week_key = f"Week {d.isocalendar()[1]}"
        month_key = d.strftime("%b %Y")

        day_logs = logs_by_date[d]

        b_logs = [l for l in day_logs if l.meal_type and "breakfast" in l.meal_type.lower()]
        l_logs = [l for l in day_logs if l.meal_type and "lunch" in l.meal_type.lower()]
        d_logs = [l for l in day_logs if l.meal_type and "dinner" in l.meal_type.lower()]

        b_logs_time = [l for l in b_logs if not is_fasting(l)]
        l_logs_time = [l for l in l_logs if not is_fasting(l)]
        d_logs_time = [l for l in d_logs if not is_fasting(l)]

        tb_daily.append(
            round(sum(get_hour_float(l.timestamp) for l in b_logs_time) / len(b_logs_time), 1) if b_logs_time else None)
        tl_daily.append(
            round(sum(get_hour_float(l.timestamp) for l in l_logs_time) / len(l_logs_time), 1) if l_logs_time else None)
        td_daily.append(
            round(sum(get_hour_float(l.timestamp) for l in d_logs_time) / len(d_logs_time), 1) if d_logs_time else None)

        qb_daily.append(sum(l.quantity or 0 for l in b_logs))
        ql_daily.append(sum(l.quantity or 0 for l in l_logs))
        qd_daily.append(sum(l.quantity or 0 for l in d_logs))

        food_b_daily.append(", ".join([l.food_name for l in b_logs if l.food_name]) or "Not logged")
        food_l_daily.append(", ".join([l.food_name for l in l_logs if l.food_name]) or "Not logged")
        food_d_daily.append(", ".join([l.food_name for l in d_logs if l.food_name]) or "Not logged")

        for log in day_logs:
            cals = log.estimated_calories or 0
            p = log.estimated_protein or 0
            c = log.estimated_carbs or 0
            f = log.estimated_fats or 0
            fib = log.estimated_fiber or 0
            m_type = log.meal_type.lower() if log.meal_type else "unknown"

            for bucket, key in [(daily_buckets, day_str), (weekly_buckets, week_key), (monthly_buckets, month_key)]:
                for target_group in ["all", m_type]:
                    if target_group in bucket[key]:
                        bucket[key][target_group]["cal"] += cals
                        bucket[key][target_group]["p"] += p
                        bucket[key][target_group]["c"] += c
                        bucket[key][target_group]["f"] += f
                        bucket[key][target_group]["fib"] += fib

    def package_timeframe_data(timeframe_bucket):
        labels = list(timeframe_bucket.keys())
        output = {
            "labels": labels,
            "high_res_labels": high_res_labels,
            "time_breakfast": tb_daily, "time_lunch": tl_daily, "time_dinner": td_daily,
            "qty_breakfast": qb_daily, "qty_lunch": ql_daily, "qty_dinner": qd_daily,
            "food_breakfast": food_b_daily, "food_lunch": food_l_daily, "food_dinner": food_d_daily
        }

        for group in ["all", "breakfast", "lunch", "dinner"]:
            output[f"calorie_{group}"] = [round(timeframe_bucket[lbl][group]["cal"]) for lbl in labels]

            tot_p = sum(timeframe_bucket[lbl][group]["p"] for lbl in labels)
            tot_c = sum(timeframe_bucket[lbl][group]["c"] for lbl in labels)
            tot_f = sum(timeframe_bucket[lbl][group]["f"] for lbl in labels)
            tot_fib = sum(timeframe_bucket[lbl][group]["fib"] for lbl in labels)
            output[f"macro_{group}"] = [round(tot_p), round(tot_c), round(tot_f), round(tot_fib)]

        return output

    # Overall Average Calories Calculation
    range_total_cals = sum(sum(l.estimated_calories or 0 for l in logs_by_date[d]) for d in daily_dates)
    avg_cals = round(range_total_cals / delta_days) if delta_days > 0 else 0

    yesterday = today - timedelta(days=1)
    yesterday_cals = MealLog.objects.filter(user=selected_username, timestamp__date=yesterday).aggregate(
        total=Sum('estimated_calories'))['total'] or 0

    # ==============================================================
    # NEW: FETCH LATEST AI HEALTH ANALYSIS
    # ==============================================================
    # Grab the most recent analysis report for the selected user
    # ==============================================================
    # NEW: FETCH LATEST AI HEALTH ANALYSIS
    # ==============================================================
    # Changed from '-created_at' to '-id' to GUARANTEE we get the absolute newest record
    latest_meta = HealthAnalysisMeta.objects.filter(user=selected_username).order_by('-id').first()

    ai_analysis_context = None
    if latest_meta:
        meal_analyses = latest_meta.meal_analyses.all()

        # 1. Force the database QuerySet into a plain list of dictionaries
        meals_list = []
        for m in meal_analyses:
            meal_dict = {
                "id": m.id,
                "meal_type": m.meal_type,
                "overall_score": m.overall_score,
                "overall_status": m.overall_status,
                "overall_ai_remarks": m.overall_ai_remarks,
                "timing_status": m.timing_status,
                "timing_metrics": m.timing_metrics,
                "timing_ai_remarks": m.timing_ai_remarks,
                "quantity_status": m.quantity_status,
                "quantity_ai_remarks": m.quantity_ai_remarks,  # <--- PINPOINT TARGET
                "portion_status": m.portion_status,
                "portion_ai_remarks": m.portion_ai_remarks,  # <--- PINPOINT TARGET
                "nutrition_status": m.nutrition_status,
                "nutrition_ai_remarks": m.nutrition_ai_remarks,
                "add_recommendations": m.add_recommendations,
                "avoid_recommendations": m.avoid_recommendations,
            }
            meals_list.append(meal_dict)

        # 2. Print the exact mapped dictionary to your Python console
        print("\n=== DEBUG: EXACT MEAL DICTIONARY SENT TO TEMPLATE ===")
        if meals_list:
            print(f"Meal: {meals_list[0]['meal_type']}")
            print(f"Quantity Remarks: {meals_list[0]['quantity_ai_remarks']}")
            print(f"Portion Remarks: {meals_list[0]['portion_ai_remarks']}")
            print(f"Nutrition Remarks: {meals_list[0]['nutrition_ai_remarks']}")
        print("======================================================\n")

        ai_analysis_context = {
            "id": latest_meta.id,
            "rating": latest_meta.health_rating,
            "score": latest_meta.health_score,
            # Converted dates to strings so JavaScript can parse them safely
            "start_time": latest_meta.start_time.strftime("%b %d, %Y"),
            "end_time": latest_meta.end_time.strftime("%b %d, %Y"),
            "no_of_meals": latest_meta.no_of_meals,
            "recommendations": [r for r in latest_meta.health_recommendation.split('\n') if r],
            "problems": [p for p in latest_meta.top_problems.split('\n') if p] if latest_meta.top_problems else [],
            "positive_patterns": [p for p in latest_meta.top_positive_patterns.split('\n') if
                                  p] if latest_meta.top_positive_patterns else [],
            # Passing our plain dictionary list instead of the Django object
            "meals": meals_list
        }

    dynamic_health_score = latest_meta.health_score if latest_meta else 0

    context = {
        "current_user": selected_username,
        "selected_username": selected_username,
        "users": usernames,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "dashboard": {
            "avg_calories": avg_cals,
            "kpi": {
                "calories_yesterday": round(yesterday_cals),
                "target_calories": 2100,
                "times_fasting": times_fasting,
                "meals_logged_actual": logs.count(),
                "meals_logged_expected": delta_days * 3,
                "streak": streak
            },
            # Updated to use the AI Score!
            "health_score": dynamic_health_score,
            "health_flags": ["Low fiber intake across segments"],
            "ai_summary": ["Consistent macro configurations monitored"],
            "charts": {
                "daily": package_timeframe_data(daily_buckets),
                "weekly": package_timeframe_data(weekly_buckets),
                "monthly": package_timeframe_data(monthly_buckets)
            }
        },
        # NEW: Injecting the AI payload for the frontend
        "ai_analysis": ai_analysis_context
    }



    return render(request, "MEDTRAC_Home.html", context)

from django.shortcuts import render
from django.contrib.auth import get_user_model
from datetime import datetime, date
import calendar


def mealdata(request):
    user = request.user
    # If no 'user' in GET, use current login user
    selected_username = request.GET.get("user", user.username)

    # Calculate month start and end if dates not provided
    today = date.today()
    _, last_day = calendar.monthrange(today.year, today.month)

    start_date = request.GET.get("start_date", f"{today.year}-{today.month:02d}-01")
    end_date = request.GET.get("end_date", f"{today.year}-{today.month:02d}-{last_day}")

    User = get_user_model()
    # Assuming family_name logic remains as per your requirement
    usernames = User.objects.filter(family_name=user.family_name).values_list("username", flat=True)

    context = {
        'current_user': user.username,
        'selected_username': selected_username,
        'usernames': list(usernames),
        'default_start': start_date,
        'default_end': end_date
    }
    return render(request, 'MEDTRAC_MealLog.html', context=context)


from django.http import JsonResponse
from django.utils.dateparse import parse_date

EXPECTED_API_KEY = "qwert"

def get_ai_nutrition_context(request):



    provided_key = request.headers.get('X-API-KEY')

    if provided_key != EXPECTED_API_KEY:
        return JsonResponse(
            {"error": "Unauthorized. Invalid or missing API Key."},
            status=401
        )


    """
    API endpoint to fetch clean, AI-ready data for a user.
    Expects GET parameters: ?user=Panisha&start_date=2026-08-01&end_date=2026-08-20
    """
    username = request.GET.get('user')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if not all([username, start_date_str, end_date_str]):
        return JsonResponse(
            {"error": "Missing required parameters: user, start_date, end_date"},
            status=400
        )

    start_date = parse_date(start_date_str)
    end_date = parse_date(end_date_str)

    # ==========================================
    # 1. Fetch & Clean Medical Profile
    # ==========================================
    profile = MedicalProfile.objects.filter(user=username).first()

    profile_data = {}
    if profile:
        profile_data = {
            "name": profile.user,
            "age": profile.age,
            "gender": profile.gender,
            "height_cm": float(profile.height_cm) if profile.height_cm else None,
            "weight_kg": float(profile.weight_kg) if profile.weight_kg else None,
            "blood_group": profile.blood_group,
            "medical_status": profile.medical_status
        }

    # ==========================================
    # 2. Fetch & Clean Meal Logs
    # ==========================================
    meals = MealLog.objects.filter(
        user=username,
        timestamp__date__gte=start_date,
        timestamp__date__lte=end_date
    )

    meals_data = []
    for meal in meals:
        meals_data.append({
            "food_name": meal.food_name,
            "quantity": meal.quantity,
            "timestamp": meal.timestamp.isoformat(),
            "meal_type": meal.meal_type,
            "is_nonveg": meal.is_nonveg,
            "estimated_calories": meal.estimated_calories,
            "estimated_protein": meal.estimated_protein,
            "estimated_carbs": meal.estimated_carbs,
            "estimated_fats": meal.estimated_fats,
            "estimated_fiber": meal.estimated_fiber,
            "estimated_sugar": meal.estimated_sugar,
            "estimated_sodium": meal.estimated_sodium,
        })

    # ==========================================
    # 3. Fetch & Clean Medical Events (NEW)
    # ==========================================
    events = MedicalEventLog.objects.filter(
        user_name=username,
        start__date__gte=start_date,
        start__date__lte=end_date
    )

    events_data = []
    for event in events:
        events_data.append({
            "medical_event": event.medical_event,
            "remarks": event.remarks,
            "start": event.start.isoformat() if event.start else None,
            "end": event.end.isoformat() if event.end else None,
            "status": event.status,
            "severity": event.severity
        })

    # ==========================================
    # 4. Return Combined JSON
    # ==========================================
    return JsonResponse({
        "profile": profile_data,
        "meals": meals_data,
        "medical_events": events_data
    })


import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import HealthAnalysisMeta, MealAnalysis




@csrf_exempt
def save_ai_analysis(request):
    """
    Receives the final JSON from the AI script and saves it to the database.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    # 1. Security Check
    provided_key = request.headers.get('X-API-KEY')
    if provided_key != EXPECTED_API_KEY:
        return JsonResponse({"error": "Unauthorized. Invalid API Key."}, status=401)

    try:
        # 2. Parse the incoming JSON payload
        data = json.loads(request.body)
        username = data.get('username')
        ai_data = data.get('ai_data')

        print(username, "ai_data")

        User = get_user_model()

        if not username or not ai_data:
            return JsonResponse({"error": "Missing 'username' or 'ai_data' in payload"}, status=400)

        user = User.objects.get(username=username)

        # 3. Save to Database (using atomic so it doesn't save half-broken data)
        with transaction.atomic():

            # Save the Meta Table
            meta_data = ai_data['Meta']
            meta_record = HealthAnalysisMeta.objects.create(
                user=username,
                start_time=meta_data.get('start_time'),
                end_time=meta_data.get('end_time'),
                health_rating=meta_data.get('health_rating'),
                health_score=meta_data.get('health_score'),
                health_recommendation=meta_data.get('health_recommendation'),
                top_problems=meta_data.get('top_problems', ''),
                top_positive_patterns=meta_data.get('top_positive_patterns', ''),
                no_of_meals=meta_data.get('no_of_meals', 0)
            )

            # Save the 4 Meal Tables using the ** dictionary unpacking trick!
            for meal_name in ['Breakfast', 'Lunch', 'Dinner', 'Snack']:
                meal_data = ai_data.get(meal_name)

                if meal_data:
                    MealAnalysis.objects.create(
                        analysis_meta=meta_record,
                        meal_type=meal_name,
                        **meal_data  # This automatically maps all 14 AI keys to your Django columns!
                    )

        return JsonResponse({"status": "success", "message": "Analysis saved to database successfully!"})

    except User.DoesNotExist:
        return JsonResponse({"error": f"User '{username}' not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def tester(requests , parameter):
    User = get_user_model()
    user = User.objects.get(username=parameter)
    print(user)
    return JsonResponse({"name": user.username})