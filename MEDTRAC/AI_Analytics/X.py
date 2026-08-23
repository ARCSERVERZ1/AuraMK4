import requests
import json
from datetime import datetime

# ==========================================================
# CONFIG
# ==========================================================

DOMAIN = "https://auraengine.pythonanywhere.com"
API_URL = f"{DOMAIN}/medtrac/api/meals/list"

USER = "Sanjay"

# ==========================================================
# DATE RANGE (Current Month)
# ==========================================================

today = datetime.today()

start_date = today.replace(day=1).strftime("%Y-%m-%d")
end_date = today.strftime("%Y-%m-%d")

print("Start Date:", start_date)
print("End Date:", end_date)

# ==========================================================
# PROMPT TEMPLATE
# ==========================================================

PROMPT_TEMPLATE = """
You are a nutrition expert for Indian cuisine.

TASK:
Estimate nutrition for each meal.

IMPORTANT:
The "quantity" field is a meal portion indicator, NOT the number of food items.

Portion Scale:
1=Very Light Bite
2=Light Bite
3=Small
4=Moderate
5=Normal
6=Filling
7=Heavy
8=Very Heavy
9=Almost Full
10=Full Stomach

Use food_name to identify the meal and quantity to adjust the serving size.

RULES:
1. Assume common Indian recipes and serving sizes.
2. Estimate:
   - estimated_calories
   - estimated_protein
   - estimated_carbs
   - estimated_fats
   - estimated_fiber
   - estimated_sugar
   - estimated_sodium
3. Keep nutrition values internally realistic.
4. Detect non-vegetarian food from food_name only.
   Return "is_nonveg":"1" for meat, fish, seafood or egg; otherwise "0".
5. Keep uid unchanged.
6. Return numeric values only.
7. Return ONLY valid JSON.
8. Do NOT include markdown or explanations.

Return format:

{
  "meals":[
    {
      "uid":98,
      "estimated_calories":320,
      "estimated_protein":8,
      "estimated_carbs":54,
      "estimated_fats":7,
      "estimated_fiber":3,
      "estimated_sugar":2,
      "estimated_sodium":420,
      "is_nonveg":"0"
    }
  ]
}

INPUT:

{meals}
"""
# ==========================================================
# API CALL
# ==========================================================

payload = {
    "user": USER,
    "start_date": start_date,
    "end_date": end_date,
}

print("\nFetching meals...")

response = requests.get(API_URL, params=payload, timeout=30)
response.raise_for_status()

data = response.json()

# ==========================================================
# HANDLE DIFFERENT API FORMATS
# ==========================================================

if isinstance(data, list):
    meals = data
elif isinstance(data, dict):
    meals = (
        data.get("results")
        or data.get("meals")
        or data.get("data")
        or []
    )
else:
    meals = []

# ==========================================================
# FILTER ai_analytics_req = 1
# ==========================================================

filtered_meals = []

for meal in meals:

    if meal.get("ai_analytics_req") != 1:
        continue

    filtered_meals.append({
        "uid": meal["uid"],
        "food_name": meal["food_name"],
        "quantity": meal["quantity"],
        "meal_type": meal.get("meal_type"),
        "is_nonveg": meal.get("is_nonveg"),
    })

print(f"\nMeals requiring AI analysis: {len(filtered_meals)}")

# ==========================================================
# BUILD PROMPT
# ==========================================================

prompt = PROMPT_TEMPLATE.format(
    meals=json.dumps(filtered_meals, indent=4)
)

# ==========================================================
# PRINT PROMPT
# ==========================================================

print("\n" + "=" * 80)
print("PROMPT")
print("=" * 80)
print(prompt)
print("=" * 80)