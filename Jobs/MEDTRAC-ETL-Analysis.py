import os
import sys
import json
import requests
from google import genai

# ============================================================
# CONFIGURATION
# ============================================================

BASE_DOMAIN = "https://auraengine.pythonanywhere.com/medtrac"
USERNAME = "Sanjay"
START_DATE = "2026-08-01"
END_DATE = "2026-08-20"
MODEL = "gemini-3.5-flash"
PROMPT_FILE_PATH = "MEDTRAC-PROMPT-TEMPLATE-ANALYSIS.txt"

# Your secured API keys
MEDTRAC_API_KEY = "qwert"
GEMINI_API_KEY = ""

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable is not set.")

# Initialize the Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)


# ============================================================
# 1. FETCH CONTEXT FROM DJANGO API (GET)
# ============================================================
def fetch_user_health_context(base_url, username, start_date, end_date):
    """Fetches the profile, meals, and medical events from the secured Django API."""
    api_url = f"{base_url}/api/ai-context/"

    params = {
        "user": username,
        "start_date": start_date,
        "end_date": end_date
    }

    headers = {
        "X-API-KEY": MEDTRAC_API_KEY
    }

    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"ERROR: Unable to fetch data from API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Server Response: {e.response.text}")
        return None


# ============================================================
# 2. LOAD PROMPT TEMPLATE
# ============================================================
def load_prompt_template(filepath):
    """Reads the text template from the local file."""
    if not os.path.exists(filepath):
        print(f"ERROR: Could not find '{filepath}'. Please ensure it is in the same folder.")
        sys.exit(1)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


# ============================================================
# 3. BUILD FINAL PROMPT
# ============================================================
def build_prompt(template_text, api_data, start_date, end_date):
    """Injects the profile, meals, and medical events into the text template."""

    profile_json = json.dumps(api_data.get('profile', {}), ensure_ascii=False, indent=2)
    meals_json = json.dumps(api_data.get('meals', []), ensure_ascii=False, indent=2)
    events_json = json.dumps(api_data.get('medical_events', []), ensure_ascii=False, indent=2)

    prompt = template_text.replace("{{PERSON_PROFILE}}", profile_json)
    prompt = prompt.replace("{{START_DATE}}", start_date)
    prompt = prompt.replace("{{END_DATE}}", end_date)
    prompt = prompt.replace("{{FOOD_DATA}}", meals_json)
    prompt = prompt.replace("{{MEDICAL_EVENTS}}", events_json)

    return prompt


# ============================================================
# 4. CALL AI & TRACK TOKENS
# ============================================================
class MockGeminiResponse:
    def __init__(self, text_content):
        self.text = text_content
        self.usage_metadata = None

def analyze_with_ai(prompt):
    """Calculates tokens, calls the AI, and returns the full response object."""
    print("   [Calculating prompt size...]")
    token_count = client.models.count_tokens(
        model=MODEL,
        contents=prompt
    )
    print(f"   [Calculated Prompt Tokens: {token_count.total_tokens}]")

    with open("nutrition_ai1_result.json", "r", encoding="utf-8") as f:
        file_content = f.read()

    # Return our fake response object so the rest of the script doesn't crash
    # return MockGeminiResponse(file_content)
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    print(response)
    return response


# ============================================================
# 5. PARSE AI JSON
# ============================================================
def parse_ai_response(response_text):
    """Safely extracts JSON from the AI response string."""
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("\nAI returned invalid JSON. Raw output:")
        print(text)
        return None


# ============================================================
# 6. PUSH ANALYSIS TO DJANGO (POST)
# ============================================================
def push_analysis_to_django(base_url, username, ai_json):
    """Sends the finalized AI JSON back to Django to be saved in the database tables."""
    api_url = f"{base_url}/api/ai-context/save/"

    headers = {
        "X-API-KEY": MEDTRAC_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "username": username,
        "ai_data": ai_json
    }

    print(f"\n5. Pushing AI analysis to Django for user '{username}'...")
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        print("   ✅ Successfully saved to Django database!")
        return True
    except requests.RequestException as e:
        print(f"   ❌ Failed to save to Django: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"      Server Response: {e.response.text}")
        return False


# ============================================================
# 7. MAIN ORCHESTRATION FLOW
# ============================================================
def main():
    print("=" * 60)
    print("NUTRITION AI-1 ANALYSIS PIPELINE")
    print("=" * 60)

    # 1. Fetch Data
    print(f"\n1. Fetching context for {USERNAME}...")
    api_data = fetch_user_health_context(BASE_DOMAIN, USERNAME, START_DATE, END_DATE)

    if not api_data:
        print("No data received from API. Exiting.")
        return

    meal_count = len(api_data.get('meals', []))
    event_count = len(api_data.get('medical_events', []))
    print(f"   Data received: Profile loaded, {meal_count} meals, {event_count} medical events.")

    if meal_count == 0:
        print("No meal records found to analyze. Exiting.")
        return

    # 2. Build Prompt
    print("\n2. Loading and Building AI prompt...")
    template_text = load_prompt_template(PROMPT_FILE_PATH)
    prompt = build_prompt(template_text, api_data, START_DATE, END_DATE)

    with open("nutrition_ai1_prompt_debug.txt", "w", encoding="utf-8") as f:
        f.write(prompt)
    print("   Prompt saved locally for debugging (nutrition_ai1_prompt_debug.txt).")

    # 3. Call AI
    print("\n3. Calling Gemini AI...")
    response = analyze_with_ai(prompt)

    if hasattr(response, 'usage_metadata') and response.usage_metadata:
        print("\n   --- TOKEN USAGE REPORT ---")
        print(f"   Input Tokens:  {response.usage_metadata.prompt_token_count}")
        print(f"   Output Tokens: {response.usage_metadata.candidates_token_count}")
        print(f"   Total Tokens:  {response.usage_metadata.total_token_count}")
        print("   --------------------------")

    # 4. Parse JSON
    print("\n4. Parsing AI response...")
    result = parse_ai_response(response.text)

    if result is None:
        return

    # Save local copy
    with open("nutrition_ai1_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print("   ✅ Local backup saved to: nutrition_ai1_result.json")

    # 5. Push to Django Database
    push_analysis_to_django(BASE_DOMAIN, USERNAME, result)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()