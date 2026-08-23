import requests
import json
import time

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3:8b"

# 🔹 HARD CODED CATEGORIES (from your JSON)
CATEGORIES = {
    "Food": ["Restaurant", "Biryani", "Cafe", "Hotel"],
    "Health Care": ["Medicine", "Consultation", "Treatment"],
    "Bank": ["Account Statement", "Charges"],
    "Miscellaneous": ["Unclassified"]
}


def classify_transaction(txn):
    print("\n🔎 Classifying UID:", txn["uid"], "|", txn["receiver_bank"])
    start_time = time.time()

    # 🔹 Strict Prompt
    prompt = f"""
You are a strict JSON classifier.

Transaction:
UID: {txn['uid']}
Receiver: {txn['receiver_bank']}
Amount: {txn['amount']}

Available Categories:
{json.dumps(CATEGORIES, indent=2)}

Rules:
- Choose ONLY from the given categories.
- If unsure, choose Miscellaneous -> Unclassified.
- Return ONLY valid JSON.
- No explanation.
- No markdown.
- No text outside JSON.

Format:
{{
  "uid": {txn['uid']},
  "category": "CategoryName",
  "sub_category": "SubCategoryName"
}}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        raw_output = response.json().get("response", "").strip()

        print("📦 RAW MODEL OUTPUT:")
        print(raw_output)

        if not raw_output:
            raise ValueError("Empty model response")

        # 🔹 Try JSON parse
        try:
            result = json.loads(raw_output)
        except json.JSONDecodeError:
            print("⚠ Attempting JSON recovery...")
            start = raw_output.find("{")
            end = raw_output.rfind("}") + 1
            recovered = raw_output[start:end]
            result = json.loads(recovered)

        end_time = time.time()
        print("⏱ Model Response Time:", round(end_time - start_time, 2), "sec")

        # 🔹 Validate category
        category = result.get("category")
        sub_category = result.get("sub_category")

        if category not in CATEGORIES:
            print("⚠ Invalid category from model. Forcing Miscellaneous.")
            category = "Miscellaneous"
            sub_category = "Unclassified"

        elif sub_category not in CATEGORIES[category]:
            print("⚠ Invalid sub_category. Forcing Unclassified.")
            sub_category = "Unclassified"

        final_output = {
            "uid": txn["uid"],
            "receiver_bank": txn["receiver_bank"],
            "amount": txn["amount"],
            "category": category,
            "sub_category": sub_category
        }

        print("\n✅ FINAL CLASSIFICATION:")
        print(json.dumps(final_output, indent=2))

        return final_output

    except Exception as e:
        print("❌ Classification failed:", str(e))
        return None


# 🔹 TEST WITH REAL TXN
txn = {
    "uid": 237,
    "receiver_bank": "ushodayasupermarkets USHODAYA SUPER MARKETS PVT LTD",
    "amount": 420
}

classify_transaction(txn)