import requests
import json
import os
from datetime import datetime, timedelta

class dem_classifer:
    # BASE_URL = "http://192.168.0.114:9001/dem/api/classification_data/"
    CACHE_HOURS = 6

    def __init__(self, user: str, start_date: str, end_date: str, base_url :str ):
        self.user = user
        self.start_date = start_date
        self.end_date = end_date
        self.BASE_URL = base_url
        self.filename = f"classification_data_{user}.json"

    def _is_cache_valid(self) -> bool:
        """Check if existing file is valid based on date range and timestamp."""
        if not os.path.exists(self.filename):
            return False

        with open(self.filename, "r", encoding="utf-8") as f:
            cached = json.load(f)

        meta = cached.get("meta", {})

        # Check date range
        if (
            meta.get("start_date") != self.start_date or
            meta.get("end_date") != self.end_date
        ):
            return False

        # Check timestamp freshness
        cached_time = datetime.fromisoformat(meta["timestamp"].replace("Z", ""))
        if datetime.utcnow() - cached_time > timedelta(hours=self.CACHE_HOURS):
            return False

        return True

    def _fetch_from_api(self) -> dict:
        """Fetch data from API."""
        url = (
            f"{self.BASE_URL}"
            f"?user={self.user}"
            f"&start_date={self.start_date}"
            f"&end_date={self.end_date}"
        )

        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def _save_to_file(self, data: dict):
        """Save API response with metadata."""
        payload = {
            "meta": {
                "user": self.user,
                "start_date": self.start_date,
                "end_date": self.end_date,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            "data": data
        }

        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4)

    def get_data(self) -> dict:
        """
        Main entry point:
        - returns cached data if valid
        - otherwise fetches fresh data
        """
        if self._is_cache_valid():
            with open(self.filename, "r", encoding="utf-8") as f:
                print(f"Using cached data {self.filename}")
                return json.load(f)["data"]

        print("Fetching new data from API")
        data = self._fetch_from_api()
        self._save_to_file(data)
        return data

