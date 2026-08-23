import requests
import json
import time

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3:8b"

# ==========================================================
# 🔹 FULL CATEGORY STRUCTURE (YOUR FINAL VERSION)
# ==========================================================
CATEGORIES = {
    "Civic & Legal": {
        "Certificates & Documents": ""
    },
    "Education": {
        "Books": "books, stationery, notebooks",
        "Courses": "online course, certification, training program",
        "Fees": "school fees, college fees, tuition fees"
    },
    "Entertainment": {
        "Events": "",
        "Movies": "",
        "Subscriptions": "netflix, spotify, ott subscription"
    },
    "Financial": {
        "Credit Card Bill": "credit card payment, card bill, cred",
        "Insurance Premium": "life insurance, vehicle insurance premium",
        "Investments": "mutual fund, stocks, shares, investment",
        "Loan EMI": "emi payment, loan installment",
        "Savings": "savings deposit, money saved, reserve funds"
    },
    "Food & Essentials": {
        "Daily Needs": "daily essentials, household items, soap, detergent",
        "Eating Out": "restaurant, hotel, dine out, cafe, biryani",
        "Food Delivery": "swiggy, zomato, online food order",
        "Groceries": "groceries, supermarket, kirana, ration, provisions, vegetable shop",
        "Meat & Seafood": "chicken, mutton, fish, prawns, crab, seafood",
        "Snacks": "snacks"
    },
    "Healthcare": {
        "Diagnostics": "lab test, blood test, scan, xray, diagnostics",
        "Insurance": "health insurance premium, mediclaim",
        "Medical Care": "consultation, hospital",
        "Medicines": "pharmacy, medical store, tablets, medicine",
        "Treatment": "treatment"
    },
    "Housing & Utilities": {
        "Electricity": "electricity bill, power bill, eb bill, current bill",
        "Gas": "lpg cylinder, gas refill, cooking gas, piped gas",
        "Internet": "wifi bill, broadband, fiber",
        "Mobile": "mobile recharge, phone bill, airtel, jio",
        "Rent": "house rent, monthly rent, landlord payment",
        "Water": "water bill, municipal water"
    },
    "Lifestyle": {
        "Accessories / Gear": "",
        "Clothing": "clothes shopping, apparel, garments",
        "Fitness": "gym, yoga, fitness center, sports turf, badminton academy",
        "Grooming": "salon, haircut, beauty parlour",
        "Hobbies / Games": "electronics kits, robotics, gaming, robocraze"
    },
    "Miscellaneous": {
        "Bank Charges": "bank fee, service charge, penalty",
        "Cash Withdrawal": "atm withdrawal, cash taken",
        "Gifts / Donations": "donation, gift",
        "Service Charges": "",
        "Unclassified": "unknown expense, uncategorized, other"
    },
    "Non-Countable": {
        "Family": "shared to family",
        "Lent Money": "money lent"
    },
    "Transportation": {
        "Cab / Taxi": "uber, ola, cab ride, taxi fare",
        "Fuel": "petrol, diesel, fuel station, petrol bunk, fuels",
        "Public Transport": "bus fare, metro, train ticket, auto fare",
        "Vehicle Maintenance": "service, repair, oil change, garage"
    }
}

# ==========================================================
# 🔹 KEYWORD-BASED CLASSIFIER
# ==========================================================
def keyword_classify(receiver_text):
    receiver_text = receiver_text.lower()

    for category, subcats in CATEGORIES.items():
        for subcat, keywords in subcats.items():
            if keywords:
                keyword_list = [k.strip().lower() for k in keywords.split(",")]
                for word in keyword_list:
                    if word and word in receiver_text:
                        return category, subcat

    return None, None


# ==========================================================
# 🔹 AI FALLBACK CLASSIFIER
# ==========================================================
def ai_classify(txn):
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

    response = requests.post(OLLAMA_URL, json=payload)
    raw_output = response.json().get("response", "").strip()

    try:
        result = json.loads(raw_output)
    except:
        return "Miscellaneous", "Unclassified"

    category = result.get("category")
    sub_category = result.get("sub_category")

    # Strict validation
    if category not in CATEGORIES:
        return "Miscellaneous", "Unclassified"

    if sub_category not in CATEGORIES[category]:
        return category, "Unclassified"

    return category, sub_category


# ==========================================================
# 🔹 MAIN CLASSIFICATION FUNCTION
# ==========================================================
def classify_transaction(txn):
    print("\n🔎 Classifying:", txn["receiver_bank"])
    start = time.time()

    # 1️⃣ Try keyword engine first
    category, sub_category = keyword_classify(txn["receiver_bank"])

    # 2️⃣ If not matched → AI fallback
    if not category:
        print("🤖 Using AI fallback...")
        category, sub_category = ai_classify(txn)

    end = time.time()

    final_output = {
        "uid": txn["uid"],
        "receiver_bank": txn["receiver_bank"],
        "amount": txn["amount"],
        "category": category,
        "sub_category": sub_category,
        "response_time_sec": round(end - start, 2)
    }

    print("✅ FINAL:", json.dumps(final_output, indent=2))
    return final_output


# ==========================================================
# 🔹 TEST TRANSACTION
# ==========================================================
txn = {
    "uid": 265,
    "receiver_bank": "SRI KOLALAMMA VEGITABLE SHOP",
    "amount": 42
}

ai_classify(txn)