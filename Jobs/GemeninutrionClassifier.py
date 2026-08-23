import json
import requests , sys
import time
from datetime import datetime, timedelta
from google import genai
sys.stdout.reconfigure(encoding='utf-8')
# ==========================================================
# CONFIG
# ==========================================================

API_KEY = ""

# Calculate the date for 20 days ago dynamically
START_DATE = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")

GET_MEALS_API = (
    f"https://auraengine.pythonanywhere.com/medtrac/api/meals/list/"
    f"?nutrition_pending=1&start_date={START_DATE}"
)
UPDATE_API = "https://auraengine.pythonanywhere.com/medtrac/api/meals/update/"

MODEL = "gemini-3.5-flash"

BATCH_SIZE = 50
DEBUG = True

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
1. Assume common Indian recipes.
2. Estimate:
- estimated_calories
- estimated_protein
- estimated_carbs
- estimated_fats
- estimated_fiber
- estimated_sugar
- estimated_sodium
3. Detect non-veg from food_name only.
4. Keep uid unchanged.
5. Return ONLY valid JSON.
6. Numeric values only.

Return:

{
  "meals":[]
}

INPUT:

{meals}
"""

client = genai.Client(api_key=API_KEY)


# ==========================================================
# FETCH MEALS
# ==========================================================

def fetch_meals():

    print("=" * 70)
    print("STEP 1 : Fetching Meals")
    print(f"Date Range: Since {START_DATE}")
    print("=" * 70)

    response = requests.get(GET_MEALS_API, timeout=30)
    response.raise_for_status()

    meals = response.json()

    if not isinstance(meals, list):
        raise Exception("Expected API to return a list.")

    print(f"Meals returned : {len(meals)}")

    # Keep only meals without nutrition
    pending = [
        m for m in meals
        if m.get("estimated_calories") is None
    ]

    print(f"Pending nutrition : {len(pending)}")

    pending = pending[:BATCH_SIZE]

    print(f"Processing : {len(pending)} meal(s)\n")

    if DEBUG and pending:
        print("First Meal:")
        print(json.dumps(pending[0], indent=4))
        print()

    return pending


# ==========================================================
# GEMINI
# ==========================================================

def estimate_nutrition(meals):

    print("=" * 70)
    print("STEP 2 : Gemini Estimation")
    print("=" * 70)

    prompt = PROMPT_TEMPLATE.replace(
        "{meals}",
        json.dumps(meals, indent=4)
    )

    max_retries = 3
    retry_delay = 20
    response = None

    # Retry Loop to handle 503 Errors
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )
            break  # Break out of the loop if successful

        except Exception as e:
            error_msg = str(e)
            if "503" in error_msg or "UNAVAILABLE" in error_msg:
                print(f"⚠️ 503 UNAVAILABLE: Model is overloaded.")
                if attempt < max_retries - 1:
                    print(f"Waiting {retry_delay} seconds before trying again... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    raise Exception(f"Max retries reached. Gemini API is still unavailable. Error: {e}")
            else:
                raise e  # If it's not a 503 error, fail immediately

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "").strip()

    if DEBUG:
        print("Gemini Response Preview:")
        print(text[:800])
        print()

    data = json.loads(text)

    print(f"Gemini estimated {len(data['meals'])} meals.\n")

    return data["meals"]


# ==========================================================
# UPDATE
# ==========================================================

def update_meals(meals):

    print("=" * 70)
    print("STEP 3 : Updating Database")
    print("=" * 70)

    success = 0
    failed = 0

    for meal in meals:

        uid = meal["uid"]

        payload = {
            "estimated_calories": meal["estimated_calories"],
            "estimated_protein": meal["estimated_protein"],
            "estimated_carbs": meal["estimated_carbs"],
            "estimated_fats": meal["estimated_fats"],
            "estimated_fiber": meal["estimated_fiber"],
            "estimated_sugar": meal["estimated_sugar"],
            "estimated_sodium": meal["estimated_sodium"],
            "is_nonveg": meal["is_nonveg"],
            "ai_analytics_req": 2
        }

        print("-" * 60)
        print(f"Updating UID : {uid}")

        try:

            response = requests.put(
                f"{UPDATE_API}{uid}/",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                print("✅ Success")
                success += 1
            else:
                print(f"❌ Failed ({response.status_code})")
                print(response.text)
                failed += 1

        except Exception as e:
            print("❌ Exception:", e)
            failed += 1

    print("\n" + "=" * 70)
    print(f"Updated : {success}")
    print(f"Failed  : {failed}")


# ==========================================================
# MAIN
# ==========================================================

def main():

    try:

        meals = fetch_meals()

        if not meals:
            print("\n✅ No pending meals found.")
            return

        nutrition = estimate_nutrition(meals)

        update_meals(nutrition)

        print("\n🎉 All Done!")

    except Exception as e:

        print("\nERROR")
        print(type(e).__name__)
        print(e)


if __name__ == "__main__":
    main()