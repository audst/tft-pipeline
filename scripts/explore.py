# scripts/explore.py
import os
import sys
import json
import httpx
from dotenv import load_dotenv

load_dotenv() 

RIOT_API_KEY = os.environ["RIOT_API_KEY"]
if not RIOT_API_KEY or RIOT_API_KEY.strip() == "":
    print("Error: RIOT_API_KEY is not set")
    sys.exit(1)

URL = "https://na1.api.riotgames.com/tft/league/v1/challenger"   
headers = {"X-Riot-Token": RIOT_API_KEY}

response = httpx.get(URL, headers=headers)

print(response.status_code)

if response.status_code != 200:
    print(f"Error: {response.text}")
    sys.exit(1)

response_json = response.json()

# inspect the structure of the response JSON
for header, value in response.headers.items():
    print(f"{header}: {value}")

print("Top-level keys:")
for key, value in response_json.items():
    print(f"  {key}: {type(value)}")
print(f"Number of entries: {len(response_json['entries'])}")

print("First entry:")
print(json.dumps(response_json["entries"][0], indent=2))