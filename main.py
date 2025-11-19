# main.py
import pandas as pd
import joblib
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION & MODEL LOADING ---
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

MODEL_FILE = "charge_model_final.pkl"

if os.path.exists(MODEL_FILE):
    charge_model = joblib.load(MODEL_FILE)
    print("AI model 'charge_model_final.pkl' loaded successfully.")
else:
    print(f"ERROR: Model file not found. Make sure '{MODEL_FILE}' is in the same folder.")
    charge_model = None

import simulated_db

app = FastAPI(title="AI Routing Distribution")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API DATA MODELS ---

class UserRequest(BaseModel):
    latitude: float
    longitude: float
    current_soc: int
    battery_capacity_kwh: int = 60
    
    # --- OPTIONAL FIELDS ---
    target_soc: int = 80
    charging_speed_preference: str = "Any"

class StationCost(BaseModel):
    name: str
    latitude: float
    longitude: float
    drive_time_minutes: float
    wait_time_minutes: float
    charge_time_minutes: float
    total_time_minutes: float
    charger_power_kw: float
    navigation_url: str
    route_polyline: str = "" # The "blue line" string (optional)
    
class RecommendationResponse(BaseModel):
    recommendations: List[StationCost]


# --- API ENDPOINT ---
@app.post("/api/v1/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: UserRequest):
    print(f"Received request: {request}")
    
    if charge_model is None:
        return {"error": "Model not loaded. Server is not ready."}
        
    all_stations = simulated_db.get_all_stations()
    recommendations = []

    # --- FILTER STATIONS BASED ON USER PREFERENCE ---
    
    filtered_stations = []
    if request.charging_speed_preference.lower() == "fast":
        filtered_stations = [s for s in all_stations if s["charger_type"] == "DC Fast Charger"]
    elif request.charging_speed_preference.lower() == "slow":
        filtered_stations = [s for s in all_stations if s["charger_type"] == "Level 2"]
    else:
        filtered_stations = list(all_stations)
    
    if not filtered_stations:
        return {"recommendations": []}

    # Get Drive Times
    origin = f"{request.latitude},{request.longitude}"
    drive_times = await get_drive_times(origin, filtered_stations)

    for station_name, drive_time_min in drive_times.items():
        station = next((s for s in filtered_stations if s["name"] == station_name), None)
        if not station:
            continue
        
        # Get Wait Time
        wait_time_min = 0.0
        if station["available_chargers"] == 0:
            wait_time_min = 15.0

        # Get Charge Time
        
        if request.current_soc >= request.target_soc:
            predicted_charge_min = 0.0
        else:
            model_input = pd.DataFrame([{
                "start_soc": request.current_soc,
                "target_soc": request.target_soc, # Use the user's requested target!
                "charger_max_power": station["charger_max_power"],
                "battery_capacity_kwh": request.battery_capacity_kwh
            }])
            
            predicted_charge_min = charge_model.predict(model_input)[0]

        # Calculate Total Cost
        total_cost = (drive_time_min * 1.5) + (wait_time_min * 1.5) + predicted_charge_min

        # Format: https://www.google.com/maps/dir/?api=1&origin={lat},{lon}&destination={lat},{lon}
        nav_url = f"https://www.google.com/maps/dir/?api=1&origin={request.latitude},{request.longitude}&destination={station['latitude']},{station['longitude']}&travelmode=driving"

        recommendations.append(StationCost(
            name=station["name"],
            latitude=station["latitude"],
            longitude=station["longitude"],
            drive_time_minutes=drive_time_min,
            wait_time_minutes=wait_time_min,
            charge_time_minutes=predicted_charge_min,
            total_time_minutes=total_cost,
            charger_power_kw=station["charger_max_power"],
            navigation_url=nav_url
        ))

    # Sort by lowest cost and return
    sorted_recs = sorted(recommendations, key=lambda s: s.total_time_minutes)

    if len(sorted_recs) > 0:
        best_station = sorted_recs[0]
        origin_str = f"{request.latitude},{request.longitude}"
        dest_str = f"{best_station.latitude},{best_station.longitude}"
        
        best_station.route_polyline = await get_route_polyline(origin_str, dest_str)
    
    return {"recommendations": sorted_recs}


# --- HELPER FUNCTION TO CALL GOOGLE MAPS ---

async def get_drive_times(origin: str, stations: list) -> dict:
    """
    Calls the Google Distance Matrix API to get real-time drive times.
    """
    if not GOOGLE_MAPS_API_KEY:
        print("WARNING: Google Maps API Key not set. Returning FAKE drive times.")
        return {s["name"]: (5 + hash(s["name"]) % 15) for s in stations}
    
    destinations = "|".join([f"{s['latitude']},{s['longitude']}" for s in stations])
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    
    params = {
        "origins": origin,
        "destinations": destinations,
        "key": GOOGLE_MAPS_API_KEY,
        "departure_time": "now"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
        except httpx.RequestError as e:
            print(f"Error calling Google Maps API: {e}")
            return {s["name"]: 999.0 for s in stations}
    
    if response.status_code != 200:
        print(f"Error from Google Maps API: {response.text}")
        return {s["name"]: 999.0 for s in stations}

    data = response.json()
    results = {}
    
    if data["status"] == "OK":
        for i, station in enumerate(stations):
            element = data["rows"][0]["elements"][i]
            if element["status"] == "OK":
                drive_time_min = element["duration_in_traffic"]["value"] / 60
                results[station["name"]] = drive_time_min
            else:
                results[station["name"]] = 999.0
    
    return results

# --- Calls Google Directions API to get the "overview_polyline" (the blue line path). ---

async def get_route_polyline(origin: str, destination: str) -> str:
    if not GOOGLE_MAPS_API_KEY:
        return "fake_polyline_string_for_testing"

    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "key": GOOGLE_MAPS_API_KEY,
        "mode": "driving"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        
    if data["status"] == "OK" and len(data["routes"]) > 0:
        # This encoded string contains all the lat/lon points of the route
        return data["routes"][0]["overview_polyline"]["points"]
    
    return ""

# --- ROOT ENDPOINT FOR TESTING ---
@app.get("/")
def read_root():
    return {"message": "AI Routing Distribution is running. Go to /docs to see the API."}