import requests
import os , time
import json

# 🔐 Store your API key in environment variable
# Windows: set RAPIDAPI_KEY=your_key
# Mac/Linux: export RAPIDAPI_KEY=your_key

API_KEY = '8d786fff23msh73313475c338f2ap171b2djsn1f84c5807f6f'

if not API_KEY:
    raise ValueError("❌ RAPIDAPI_KEY not found in environment variables")

URL = "https://nutrition-tracker-api.p.rapidapi.com/v1/calculate/natural"

headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "nutrition-tracker-api.p.rapidapi.com",
    "Content-Type": "application/json"
}

def get_nutrition(food_text: str, retries=3):
    payload = {"text": food_text}

    for attempt in range(retries):
        try:
            response = requests.post(URL, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                return response.json()

            if response.status_code == 504:
                print("⚠️ Timeout... retrying...")
                time.sleep(2)
                continue

            return {
                "error": f"API Error {response.status_code}",
                "details": response.text
            }

        except requests.exceptions.RequestException as e:
            return {"error": "Request failed", "details": str(e)}

    return {"error": "API unavailable after retries"}
# 🔄 Example usage
if __name__ == "__main__":
    food_input = input("Enter food description: ")

    result = get_nutrition(food_input)

    print("\n📊 Response:\n")
    print(json.dumps(result, indent=4))