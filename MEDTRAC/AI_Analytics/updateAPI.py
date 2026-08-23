import requests

# Your JSON payload
payload = {
    "meals": [
        {
            "uid": 126,
            "estimated_calories": 1500,
            "estimated_protein": 60,
            "estimated_carbs": 210,
            "estimated_fats": 48,
            "estimated_fiber": 12,
            "estimated_sugar": 6,
            "estimated_sodium": 2100
        },
        {
            "uid": 125,
            "estimated_calories": 1120,
            "estimated_protein": 24,
            "estimated_carbs": 200,
            "estimated_fats": 24,
            "estimated_fiber": 16,
            "estimated_sugar": 8,
            "estimated_sodium": 1800
        }
    ]
}

BASE_URL = "https://auraengine.pythonanywhere.com/medtrac/api/meals/update/"

# Loop and update each meal via your existing API
for meal in payload["meals"]:
    uid = meal["uid"]
    url = f"{BASE_URL}{uid}/"

    response = requests.put(url, json=meal)

    if response.status_code == 200:
        print(f"Successfully updated meal UID: {uid}")
    else:
        print(f"Failed to update meal UID: {uid}. Error: {response.text}")