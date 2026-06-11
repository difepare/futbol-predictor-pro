# test_api.py
import requests

API_KEY = "9e346e18701e4928f7cd1eeee3d8d510"  # <-- PON TU API KEY REAL
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

# Probar status
response = requests.get(f"{BASE_URL}/status", headers=HEADERS)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")