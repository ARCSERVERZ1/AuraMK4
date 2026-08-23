import requests
import json
import time

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3:8b"


# ===============================
# HARDCODED CATEGORY STRUCTURE
# ===============================

CATEGORIES = [
    {"category": "Civic & Legal", "sub_category": "Certificates & Documents", "notes": ""},
    {"category": "Education", "sub_category": "Booooks", "notes": "books, stationery, notebooks"},
    {"category": "Education", "sub_category": "Courses", "notes": "online course, certification, training program"},
    {"category": "Education", "sub_category": "Fees", "notes": "school fees, college fees, tuition fees"},
    {"category": "Entertainment", "sub_category": "Events", "notes": ""},
    {"category": "Entertainment", "sub_category": "Movies", "notes": ""},
    {"category": "Entertainment", "sub_category": "Subscriptions", "notes": "netflix, spotify, ott subscription"},
    {"category": "Financial", "sub_category": "Credit Card Bill", "notes": "credit card payment, card bill, cred"},
    {"category": "Financial", "sub_category": "Insurance Premium", "notes": "life insurance, vehicle insurance premium"},
    {"category": "Financial", "sub_category": "Investments", "notes": "mutual fund, stocks, shares, investment"},
    {"category": "Financial", "sub_category": "Loan EMI", "notes": "emi payment, loan installment"},
    {"category": "Financial", "sub_category": "Savings", "notes": "savings deposit, reserve funds"},
    {"category": "Food & Essentials", "sub_category": "Daily Needs", "notes": "household items, soap, detergent"},
    {"category": "Food & Essentials", "sub_category": "Eating Out", "notes": "restaurant, hotel food, dine out, cafe, biryani"},
    {"category": "Food & Essentials", "sub_category": "Food Delivery", "notes": "swiggy, zomato, online food order"},
    {"category": "Food & Essentials", "sub_category": "Groceries", "notes": "supermarket, kirana, vegetables"},
    {"category": "Food & Essentials", "sub_category": "Meat & Seafood", "notes": "chicken, mutton, fish, seafood"},
    {"category": "Food & Essentials", "sub_category": "Snacks", "notes": "snacks"},
    {"category": "Healthcare", "sub_category": "Diagnostics", "notes": "lab test, blood test, scan, xray"},
    {"category": "Healthcare", "sub_category": "Insurance", "notes": "health insurance, mediclaim"},
    {"category": "Healthcare", "sub_category": "Medical Care", "notes": "consultation, hospital visit"},
    {"category": "Healthcare", "sub_category": "Medicines", "notes": "pharmacy, tablets, medicine"},
    {"category": "Healthcare", "sub_category": "Treatment", "notes": "treatment"},
    {"category": "Housing & Utilities", "sub_category": "Electricity", "notes": "electricity bill, eb bill"},
    {"category": "Housing & Utilities", "sub_category": "Gas", "notes": "lpg cylinder, gas refill"},
    {"category": "Housing & Utilities", "sub_category": "Internet", "notes": "wifi, broadband"},
    {"category": "Housing & Utilities", "sub_category": "Mobile", "notes": "mobile recharge, jio, airtel"},
    {"category": "Housing & Utilities", "sub_category": "Rent", "notes": "house rent, landlord"},
    {"category": "Housing & Utilities", "sub_category": "Water", "notes": "water bill"},
    {"category": "Lifestyle", "sub_category": "Accessories / Gear", "notes": ""},
    {"category": "Lifestyle", "sub_category": "Clothing", "notes": "clothes, apparel"},
    {"category": "Lifestyle", "sub_category": "Fitness", "notes": "gym, fitness center, badminton academy"},
    {"category": "Lifestyle", "sub_category": "Grooming", "notes": "salon, haircut"},
    {"category": "Lifestyle", "sub_category": "Hobbies / Games", "notes": ""},
    {"category": "Miscellaneous", "sub_category": "Bank Charges", "notes": "bank fee, penalty"},
    {"category": "Miscellaneous", "sub_category": "Cash Withdrawal", "notes": "atm withdrawal"},
    {"category": "Miscellaneous", "sub_category": "Gifts / Donations", "notes": "donation"},
    {"category": "Miscellaneous", "sub_category": "Service Charges", "notes": ""},
    {"category": "Miscellaneous", "sub_category": "Unclassified", "notes": "unknown expense"},
    {"category": "Non-Countable", "sub_category": "Family", "notes": "shared to family"},
    {"category": "Non-Countable", "sub_category": "Lent Money", "notes": "money lent"},
    {"category": "Transportation", "sub_category": "Cab / Taxi", "notes": "uber, ola, taxi"},
    {"category": "Transportation", "sub_category": "Fuel", "notes": "petrol, diesel, fuel station"},
    {"category": "Transportation", "sub_category": "Public Transport", "notes": "bus, metro, train"},
    {"category": "Transportation", "sub_category": "Vehicle Maintenance", "notes": "repair, service"}
]


# ===============================
# CLASSIFIER FUNCTION
# ===============================

def classify_transaction(transaction):

    print("\n🚀 Classifying Transaction")
    print("--------------------------------------------------")
    print(json.dumps(transaction, indent=2))

    prompt = f"""
You are an expert financial classifier.

Use merchant name + notes intelligently.

You MUST choose ONE category + sub_category from the provided list.
Do NOT create new categories.

Return confidence:
90-100 = exact keyword match
70-89 = strong business match
50-69 = reasonable guess
Below 50 = weak guess

AVAILABLE CATEGORIES:
{json.dumps(CATEGORIES, indent=2)}

TRANSACTION:
{json.dumps(transaction, indent=2)}

Return ONLY JSON:

{{
  "uid": {transaction["uid"]},
  "category": "...",
  "sub_category": "...",
  "confidence_percent": 85,
  "reason": "short explanation"
}}
"""

    start = time.time()

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "temperature": 0,
            "stream": False
        },
        timeout=120
    )

    raw_output = response.json().get("response", "").strip()

    print("\n📦 RAW OUTPUT:")
    print(raw_output)

    try:
        result = json.loads(raw_output)
        print("\n✅ FINAL RESULT:")
        print(json.dumps(result, indent=2))
        print(f"\n⏱ Time Taken: {round(time.time() - start, 2)} sec")
        return result
    except:
        print("\n❌ JSON Parse Failed")
        return None


# ===============================
# TEST SINGLE RECORD
# ===============================

if __name__ == "__main__":

    test_transaction = {
        "uid": 267,
        "receiver_bank": "littl787172972@barodampay LITTLE ENGLAND BADMINTON ACADEMY",
        "amount": 898
    }

    classify_transaction(test_transaction)