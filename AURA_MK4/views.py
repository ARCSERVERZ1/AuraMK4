
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse
from APPGROUP.models import *
import json
from datetime import timedelta
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt  # Optional: only if calling from outside Django

def test(request):
    locations = list(LocationLog.objects.all().values())
    return JsonResponse({'test':locations})


@csrf_exempt
@require_POST
def auto_log_location(request):
    try:
        # 1. Parse the JSON payload sent by your API/fetch
        data = json.loads(request.body)

        # 2. Extract the variables
        user_val = data.get('user', '')
        place_name = ''
        status_val = 'Page-Invoke'
        visibility = 10
        remarks = data.get('remarks', '')
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        # 3. Basic Validation (Check before using coordinates)
        # if not user_val:
        #     return JsonResponse({'status': 'error', 'message': 'User identifier is required'}, status=400)

        if not latitude or not longitude:
            return JsonResponse({'status': 'error', 'message': 'Missing coordinates'}, status=400)

        # 4. Safely build the map URL after validation
        map_url = f"https://maps.google.com/?q={latitude},{longitude}"

        # 5. One-Hour Log Condition Check
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_log_exists = LocationLog.objects.filter(
            user=user_val,
            timestamp__gte=one_hour_ago,
            status='Page-Invoke'
        ).exists()

        if recent_log_exists:
            # Return success, but skip database creation to prevent spam
            return JsonResponse({
                'status': 'ignored',
                'message': 'Location already logged within the last hour.'
            }, status=200)

        # 6. Create and save the record to the database
        log = LocationLog.objects.create(
            user=user_val,
            place_name=place_name,
            status=status_val,
            visibility=int(visibility),
            remarks=remarks,
            latitude=str(latitude),
            longitude=str(longitude),
            map_url=map_url
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Location logged successfully',
            'log_id': log.uid
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid data type for visibility'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid credentials")

    return render(request, "Login_Page.html")


@login_required
def home(request):
    return render(request, "Home.html")

def logout_view(request):
    logout(request)
    return redirect("login")  # redirect to login page