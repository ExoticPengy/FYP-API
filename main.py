# main.py
import pandas as pd
import joblib
import math
import os
import httpx
import polyline
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import simulated_db 

# --- 1. CONFIGURATION ---
load_dotenv()
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
MODEL_FILE = "charge_model_final.pkl"
AVG_CONSUMPTION_KWH_KM = 0.2

charge_model = None
if os.path.exists(MODEL_FILE):
    try:
        charge_model = joblib.load(MODEL_FILE)
        print(f"✅ AI Model '{MODEL_FILE}' loaded successfully.")
    except Exception as e:
        print(f"⚠️ Error loading model: {e}")
else:
    print(f"⚠️ Warning: '{MODEL_FILE}' not found. Using physics fallback.")

app = FastAPI(title="AI Routing Distribution")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. DATA MODELS ---
class TripRequest(BaseModel):
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    current_soc: int = 20
    target_soc: int = 80
    battery_capacity_kwh: int = 60
    preferred_speed: str = "any"

# --- 3. MATH HELPERS ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371 
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def predict_time(station, req: TripRequest):
    try:
        if charge_model:
            features = pd.DataFrame([{
                'current_soc': req.current_soc,
                'target_soc': req.target_soc,
                'battery_capacity_kwh': req.battery_capacity_kwh,
                'charger_max_power': station['charger_max_power']
            }])
            return round(charge_model.predict(features)[0], 1)
    except Exception:
        pass
    
    energy_needed = (req.target_soc - req.current_soc) / 100 * req.battery_capacity_kwh
    power = station.get('charger_max_power', 50)
    if power <= 0: return 999
    return round((energy_needed / power) * 60, 1)

def estimate_cost(kwh_needed, station):
    if station['charger_type'] == 'AC':
        rate = 1.00
    elif station['charger_max_power'] >= 100:
        rate = 1.60
    else:
        rate = 1.40
    return round(kwh_needed * rate, 2)

# --- 4. GOOGLE MAPS HELPER ---
async def fetch_route_data(start_lat, start_lng, end_lat, end_lng, stop_lat, stop_lng):
    if GOOGLE_MAPS_API_KEY:
        try:
            url = "https://maps.googleapis.com/maps/api/directions/json"
            params = {
                "origin": f"{start_lat},{start_lng}",
                "destination": f"{end_lat},{end_lng}",
                "waypoints": f"{stop_lat},{stop_lng}", 
                "key": GOOGLE_MAPS_API_KEY,
                "mode": "driving"
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params)
                data = resp.json()
                
                if data["status"] == "OK":
                    route = data["routes"][0]
                    total_meters = sum(leg["distance"]["value"] for leg in route["legs"])
                    total_seconds = sum(leg["duration"]["value"] for leg in route["legs"])

                    return {
                        "polyline": route["overview_polyline"]["points"],
                        "duration_min": round(total_seconds / 60, 1),
                        "distance_km": round(total_meters / 1000, 1)
                    }
                else:
                    print(f"⚠️ Google API Status: {data['status']}")
        except Exception as e:
            print(f"⚠️ API Connection Error: {e}")

    # Fallback
    print("⚠️ Using Simulation Fallback")
    points = [(start_lat, start_lng), (stop_lat, stop_lng), (end_lat, end_lng)]
    dist_km = haversine(start_lat, start_lng, stop_lat, stop_lng) + haversine(stop_lat, stop_lng, end_lat, end_lng)
    
    return {
        "polyline": polyline.encode(points), 
        "duration_min": round((dist_km / 80) * 60, 1),
        "distance_km": round(dist_km, 1)
    }

# --- 5. MAIN API ENDPOINT ---
@app.post("/recommendations")
async def get_recommendations(req: TripRequest):
    mid_lat = (req.start_lat + req.end_lat) / 2
    mid_lng = (req.start_lng + req.end_lng) / 2
    
    candidates = []
    
    # 1. Range Calculations
    current_kwh = (req.current_soc / 100) * req.battery_capacity_kwh
    max_range_km = current_kwh / AVG_CONSUMPTION_KWH_KM
    safe_buffer_km = (0.05 * req.battery_capacity_kwh) / AVG_CONSUMPTION_KWH_KM
    safe_driveable_km = max_range_km - safe_buffer_km
    if safe_driveable_km < 10: safe_driveable_km = 10 
    
    energy_needed_kwh = (req.target_soc - req.current_soc) / 100 * req.battery_capacity_kwh
    if energy_needed_kwh < 0: energy_needed_kwh = 0

    # 2. Main Loop (Standard Midpoint Strategy)
    for station_id, station in simulated_db.STATIONS_DB.items():
        power = station['charger_max_power']
        
        if req.preferred_speed == "fast" and power < 50: continue
        if req.preferred_speed == "ultrafast" and power < 100: continue

        dist_from_start = haversine(req.start_lat, req.start_lng, station['latitude'], station['longitude'])
        
        # Strict Range Check
        if dist_from_start > safe_driveable_km:
            continue

        dist_from_mid = haversine(mid_lat, mid_lng, station['latitude'], station['longitude'])
        if dist_from_mid <= 100: 
            item = station.copy()
            item['detour_km'] = round(dist_from_mid, 1)
            item['estimated_time_min'] = predict_time(station, req)
            item['energy_added_kwh'] = round(energy_needed_kwh, 2)
            item['estimated_cost_myr'] = estimate_cost(energy_needed_kwh, station)
            
            score = dist_from_mid + (item['estimated_time_min'] * 0.5)
            if station['status'] != 'Available': score += 200
            elif power >= 120: score -= 15
            
            item['score'] = round(score, 2)
            item['note'] = "✅ Standard Option"
            candidates.append(item)

    # 3. Emergency Fallback (Reachable but ignored Speed Prefs)
    if not candidates:
        print("⚠️ No ideal chargers. Searching for ANY reachable charger near start...")
        for station_id, station in simulated_db.STATIONS_DB.items():
            dist_from_start = haversine(req.start_lat, req.start_lng, station['latitude'], station['longitude'])
            
            if dist_from_start <= safe_driveable_km:
                item = station.copy()
                item['detour_km'] = round(dist_from_start, 1)
                item['estimated_time_min'] = predict_time(station, req)
                item['energy_added_kwh'] = round(energy_needed_kwh, 2)
                item['estimated_cost_myr'] = estimate_cost(energy_needed_kwh, station)
                item['score'] = dist_from_start 
                item['note'] = "⚠️ Emergency Stop (Reachable)"
                candidates.append(item)

    # 4. ABSOLUTE LAST RESORT (If even emergency search failed)
    if not candidates:
        print("⚠️ CRITICAL: No reachable chargers found. Returning absolute closest.")
        closest_station = None
        min_dist = float('inf')

        for station_id, station in simulated_db.STATIONS_DB.items():
            d = haversine(req.start_lat, req.start_lng, station['latitude'], station['longitude'])
            if d < min_dist:
                min_dist = d
                closest_station = station

        if closest_station:
            item = closest_station.copy()
            item['detour_km'] = round(min_dist, 1)
            item['estimated_time_min'] = predict_time(closest_station, req)
            item['energy_added_kwh'] = round(energy_needed_kwh, 2)
            item['estimated_cost_myr'] = estimate_cost(energy_needed_kwh, closest_station)
            item['score'] = min_dist
            item['note'] = "❌ OUT OF RANGE (Closest Option)"
            candidates.append(item)

    # 5. Sort & Finalize
    candidates.sort(key=lambda x: x['score'])
    top_5 = candidates[:5]

    final_results = []
    trip_polyline = None
    charger_stop_info = None
    trip_total_dist = 0
    trip_total_time = 0
    
    for i, station in enumerate(top_5):
        station['maps_url'] = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={req.start_lat},{req.start_lng}"
            f"&destination={req.end_lat},{req.end_lng}"
            f"&waypoints={station['latitude']},{station['longitude']}"
            f"&travelmode=driving"
        )
        
        if i == 0:
            route_info = await fetch_route_data(
                req.start_lat, req.start_lng,
                req.end_lat, req.end_lng,
                station['latitude'], station['longitude']
            )
            station['polyline'] = route_info['polyline']
            station['real_traffic_duration_min'] = route_info['duration_min']
            trip_polyline = route_info['polyline']
            trip_total_dist = route_info['distance_km']
            trip_total_time = route_info['duration_min']
            
            charger_stop_info = {
                "lat": station["latitude"],
                "lng": station["longitude"],
                "name": station["name"],
                "cost_est": station["estimated_cost_myr"],
                "kwh_est": station["energy_added_kwh"]
            }
        else:
            station['polyline'] = None 
            station['real_traffic_duration_min'] = station['estimated_time_min'] 
        
        final_results.append(station)

    return {
        "trip": {
            "origin": {"lat": req.start_lat, "lng": req.start_lng},
            "destination": {"lat": req.end_lat, "lng": req.end_lng},
            "charger_stop": charger_stop_info,
            "midpoint": {"lat": mid_lat, "lng": mid_lng},
            "polyline": trip_polyline,
            "total_distance_km": trip_total_dist,
            "total_duration_min": trip_total_time,
            "max_safe_range_km": round(safe_driveable_km, 1)
        },
        "options": final_results
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 AI Service Running on Port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)