import json
import random
import requests

# Load restaurants data
with open("restaurants.json") as f:
    RESTAURANTS = json.load(f)

# Preprocessing
RESTAURANTS_BY_ID = {r["id"]: r for r in RESTAURANTS}
RESTAURANTS_BY_NAME = {r["name"].lower(): r for r in RESTAURANTS}
RESERVATIONS = {}

# --- Helpers ---

def call_llama(message):
    prompt = f"""
You are a restaurant reservation assistant. Your job is to extract the intent and data from the user's message.

Return valid JSON only in this format:
{{
  "intent": "search" | "book" | "other" | "suggest" | "more_suggestions",
  "cuisine": string or null,
  "location": string or null,
  "ambiance": string or null,
  "restaurant_name": string or null,
  "date": "YYYY-MM-DD" or null,
  "time": "HH:MM" or null,
  "name": string or null,
  "party_size": integer or null
}}

User: "{message}"
"""

    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are a helpful restaurant reservation assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        text = res.json()["choices"][0]["message"]["content"]
        return json.loads(text)
    except Exception as e:
        print(f"Error: {e}")
        return {"intent": "other"}

def search_restaurants(cuisine=None, location=None, ambiance=None):
    results = RESTAURANTS
    if cuisine:
        results = [r for r in results if cuisine in r["cuisine"]]
    if location:
        results = [r for r in results if r["location"].lower() == location.lower()]
    if ambiance:
        results = [r for r in results if ambiance.lower() in r["ambiance"].lower()]
    return results

def get_available_slots(restaurant_id, date):
    key = f"{restaurant_id}_{date}"
    return RESERVATIONS.get(key, {})

def make_reservation(restaurant_id, date, time, name, party_size):
    key = f"{restaurant_id}_{date}"
    if key not in RESERVATIONS:
        RESERVATIONS[key] = {}
    if time not in RESTAURANTS_BY_ID[restaurant_id]["available_times"]:
        return False
    if time in RESERVATIONS[key]:
        return False
    RESERVATIONS[key][time] = {"name": name, "party_size": party_size}
    return True
