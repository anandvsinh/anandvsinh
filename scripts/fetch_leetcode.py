import json
import requests
from datetime import datetime, timezone
from pathlib import Path

USERNAME = "anandvsinh"
YEAR = datetime.now(timezone.utc).year

URL = "https://leetcode.com/graphql"

QUERY = """
query userProfileCalendar($username: String!, $year: Int) {
    matchedUser(username: $username) {
        username
        profile {
            realName
        }
        userCalendar(year: $year) {
            activeYears
            streak
            totalActiveDays
            submissionCalendar
        }
    }
}
"""

payload = {
    "query": QUERY,
    "variables": {
        "username": USERNAME,
        "year": YEAR
    }
}

headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

response = requests.post(
    URL,
    json=payload,
    headers=headers,
    timeout=30
)

response.raise_for_status()

data = response.json()

if "errors" in data:
    raise RuntimeError(json.dumps(data["errors"], indent=2))

user = data["data"]["matchedUser"]

if user is None:
    raise RuntimeError(
        f"LeetCode user '{USERNAME}' was not found."
    )

calendar = user["userCalendar"]

submission_calendar = json.loads(
    calendar["submissionCalendar"]
)

output = {
    "username": USERNAME,
    "year": YEAR,
    "fetched_at": datetime.now(timezone.utc).isoformat(),

    "streak": calendar["streak"],
    "total_active_days": calendar["totalActiveDays"],
    "active_years": calendar["activeYears"],

    "submission_calendar": submission_calendar
}

output_path = Path("leetcode_data.json")

output_path.write_text(
    json.dumps(output, indent=2),
    encoding="utf-8"
)

print("========================================")
print("       LEETCODE DATA FETCHED")
print("========================================")
print(f"Username       : {USERNAME}")
print(f"Year           : {YEAR}")
print(f"Current streak : {calendar['streak']}")
print(f"Active days    : {calendar['totalActiveDays']}")
print(f"Calendar days  : {len(submission_calendar)}")
print("========================================")
