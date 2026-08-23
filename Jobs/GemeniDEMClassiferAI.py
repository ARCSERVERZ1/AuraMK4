import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

from google import genai
from google.genai import errors

# ==========================================================
# PATHS
# ==========================================================

HOME = Path(__file__).resolve().parent

# ==========================================================
# CONFIG
# ==========================================================

DOMAIN = "https://auraengine.pythonanywhere.com"

API_GET_UNCLASSIFIED_DATA = f"{DOMAIN}/dem/api/ai_analytics"
API_BULK_UPDATE = f"{DOMAIN}/dem/api/bulk-update-transactions/"

API_KEY = ""
MODEL = "gemini-3.5-flash"

PROMPT_TEMPLATE_FILE = HOME / "DEM_AI_CLASSIFIER_PT.txt"

USER_NAMES = [
    "Sanjay",
    "Avinash"
]

RUNS_PER_USER = 1

# Retry settings
MAX_RETRIES = 1000000          # Effectively infinite retries
RETRY_DELAY = 60               # Seconds

# ==========================================================
# DATE RANGE
# ==========================================================

end_date = datetime.today().date()
start_date = end_date - timedelta(days=20)

START_DATE = start_date.strftime("%Y-%m-%d")
END_DATE = end_date.strftime("%Y-%m-%d")

# ==========================================================
# GEMINI CLIENT
# ==========================================================

client = genai.Client(api_key=API_KEY)

# ==========================================================
# BUILD PROMPT
# ==========================================================

def build_prompt(api_data):

    with open(PROMPT_TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()

    prompt = template.format(
        category=json.dumps(api_data["category"], indent=2),
        transactions=json.dumps(api_data["Txns"], indent=2)
    )

    return prompt

# ==========================================================
# GEMINI CLASSIFICATION
# ==========================================================

def classify_transactions(api_data):

    prompt = build_prompt(api_data)

    attempt = 1

    while attempt <= MAX_RETRIES:

        try:

            print(f"Sending request to Gemini (Attempt {attempt})...")

            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )

            text = response.text.strip()

            if text.startswith("```"):
                text = (
                    text.replace("```json", "")
                        .replace("```", "")
                        .strip()
                )

            data = json.loads(text)

            txns = data.get("classified_transactions", [])

            print(f"Gemini classified {len(txns)} transactions.")

            return txns

        except errors.ServerError as e:

            if "503" in str(e) or "UNAVAILABLE" in str(e):

                print(e)

                print("=" * 80)
                print("Gemini is currently busy (503 UNAVAILABLE).")
                print(f"Waiting {RETRY_DELAY} seconds before retrying...")
                print("=" * 80)

                time.sleep(RETRY_DELAY)
                attempt += 1
                continue

            raise

        except Exception:
            raise

    raise Exception("Maximum retry limit exceeded.")

# ==========================================================
# BULK UPDATE
# ==========================================================

def bulk_update(transactions):

    print("Updating database...")

    response = requests.post(
        API_BULK_UPDATE,
        json=transactions,
        timeout=120
    )

    response.raise_for_status()

    print("Bulk Update Successful")

# ==========================================================
# PROCESS USER
# ==========================================================

def process_user(user_name):

    for run in range(1, RUNS_PER_USER + 1):

        print("\n" + "=" * 80)
        print(f"User : {user_name}")
        print(f"Run  : {run}")
        print("=" * 80)

        payload = {
            "user": user_name,
            "start_date": START_DATE,
            "end_date": END_DATE
        }

        print("Fetching transactions...")

        response = requests.post(
            API_GET_UNCLASSIFIED_DATA,
            data=payload,
            timeout=60
        )

        response.raise_for_status()

        api_data = response.json()

        txns = api_data.get("Txns", [])

        print(f"Transactions fetched : {len(txns)}")

        if not txns:
            print("No transactions found.")
            break

        classified = classify_transactions(api_data)

        if not classified:
            print("Gemini returned no classifications.")
            break

        bulk_update(classified)

        print("Run completed.")

# ==========================================================
# MAIN
# ==========================================================

def main():

    print("=" * 80)
    print("Aura AI Classification")
    print("=" * 80)

    for user in USER_NAMES:
        process_user(user)

    print("\nFinished.")

# ==========================================================
# ENTRY
# ==========================================================

if __name__ == "__main__":
    main()