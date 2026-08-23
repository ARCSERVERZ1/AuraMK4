import json
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from rest_framework import viewsets
from .models import *
from .serializers import *
from django.contrib.auth import get_user_model
from collections import defaultdict
from django.contrib.auth.decorators import login_required # Adds security
from django.db.models import Q



def userlist_and_current_user(request):
    user = request.user
    family_name = user.family_name
    User = get_user_model()
    usernames = User.objects.filter(family_name=family_name).values_list("username", flat=True)
    return {
        'usernames': usernames,
        'user': user.username,
    }


def home_auto_dashboard(request):

    user_from_func = userlist_and_current_user(request)

    user = user_from_func['user']

    default_house = (
        UserHouseMapping.objects
        .filter(user=user, is_active=True)
        .values_list('house', flat=True)
        .first()
    )
    print(default_house)
    queryset = (
        HomeAutomation.objects
        .filter(is_active=True)
        .order_by(
            "House",
            "room",
            "device_name",
            "display_order"
        )
    )

    nested_data = defaultdict(lambda: defaultdict(list))

    for record in queryset:

        nested_data[record.House][record.room].append({
            "uid": str(record.uid),
            "House": record.House,
            "room": record.room,
            "device_name": record.device_name,
            "action": record.action,
            "api_url": record.api_url,
            "display_order": record.display_order,
            "is_active": record.is_active,
        })

    houses = []

    for house_name, rooms in nested_data.items():

        room_list = []

        for room_name, devices in rooms.items():

            room_list.append({
                "name": room_name,
                "devices": devices
            })

        houses.append({
            "house": house_name,
            "rooms": room_list
        })

    context = {
        "houses": houses ,

        "defaultHouse": default_house,
    }

    return render(
        request,
        "APPG_home_auto_dashboard.html",
        context
    )



class HomeAutomationViewSet(viewsets.ModelViewSet):
    """
    Handles all Create (Add), Read, Update (Edit), and Delete API operations automatically.
    """
    queryset = HomeAutomation.objects.all().order_by(
        "room",
        "device_name",
        "display_order"
    )
    serializer_class = HomeAutomationSerializer


# import your HomeAutomation model

@login_required # Ensure random visitors cannot hit this endpoint
@require_POST
def trigger_home_auto_action(request):
    """
    Retrieves the device API URL securely from the database
    and passes it to the frontend for client-side execution.
    """
    try:
        data = json.loads(request.body)
        uid = data.get('uid')

        if not uid:
            return JsonResponse({"status": "error", "message": "Missing UID mapping"}, status=400)

        # Retrieve the specific action record
        device_action = HomeAutomation.objects.get(uid=uid)

        # INSTEAD of calling requests.get(), we return the URL to the authorized client
        return JsonResponse({
            "status": "success",
            "message": f"URL retrieved securely-{device_action.api_url}",
            "api_url": device_action.api_url,
            "action_name": device_action.action,
            "device_name": device_action.device_name
        })

    except HomeAutomation.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Device action not found in database"}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON payload"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


class HomeAutomationViewSet(viewsets.ModelViewSet):
    queryset = HomeAutomation.objects.all().order_by(
        "room",
        "device_name",
        "display_order"
    )
    serializer_class = HomeAutomationSerializer



class LocationLogViewSet(viewsets.ModelViewSet):
    queryset = LocationLog.objects.all()
    serializer_class = LocationLogSerializer

from django.shortcuts import render


def location_log_dashboard(request):
    user_from_func = userlist_and_current_user(request)

    user = user_from_func['user']
    usernames = user_from_func['usernames']
    print(user , list(usernames))




    locations = LocationLog.objects.filter(
        user__in=usernames
    ).exclude(
        status='Page-Invoke'
    ).filter(
        ~Q(visibility=1) | Q(user=user)
    )

    serializer = LocationLogSerializer(locations, many=True)
    # Pass as JSON string to the template context
    context = {
        'locations_json': json.dumps(serializer.data)
    }
    # return render(request, 'location_dashboard.html', context)
    return render(request, "APPG_LocationsHome.html", context)