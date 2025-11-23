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

# --- CONFIGURATION ---
load_dotenv()
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
MODEL_FILE = "charge_model_final.pkl"

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

# --- DATA MODELS ---
class TripRequest(BaseModel):
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    current_soc: int = 20
    target_soc: int = 80
    battery_capacity_kwh: int = 60
    preferred_speed: str = "any"

# --- MATH HELPERS ---
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

# --- GOOGLE MAPS HELPER ---
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
                    return {
                        "polyline": route["overview_polyline"]["points"],
                        "duration_min": round(sum(leg["duration"]["value"] for leg in route["legs"]) / 60, 1)
                    }
                else:
                    print(f"⚠️ Google API Status: {data['status']}")
        except Exception as e:
            print(f"⚠️ API Connection Error: {e}")

    print("⚠️ Using Simulation Fallback")
    points = [(start_lat, start_lng), (stop_lat, stop_lng), (end_lat, end_lng)]
    dist_km = haversine(start_lat, start_lng, stop_lat, stop_lng) + haversine(stop_lat, stop_lng, end_lat, end_lng)
    
    return {
        "polyline": polyline.encode(points), 
        "duration_min": round((dist_km / 80) * 60, 1)
    }

# --- MAIN API ENDPOINT ---
@app.post("/recommendations")
async def get_recommendations(req: TripRequest):
    mid_lat = (req.start_lat + req.end_lat) / 2
    mid_lng = (req.start_lng + req.end_lng) / 2
    
    candidates = []

    for station_id, station in simulated_db.STATIONS_DB.items():
        power = station['charger_max_power']
        
        if req.preferred_speed == "fast" and power < 50: continue
        if req.preferred_speed == "ultrafast" and power < 100: continue

        dist = haversine(mid_lat, mid_lng, station['latitude'], station['longitude'])
        
        if dist <= 100: 
            item = station.copy()
            item['detour_km'] = round(dist, 1)
            item['estimated_time_min'] = predict_time(station, req)
            
            score = dist + (item['estimated_time_min'] * 0.5)
            
            if station['status'] != 'Available': 
                score += 200
                item['note'] = f"⚠️ {station['status']}"
            elif power >= 120: 
                score -= 15
                item['note'] = "⚡ Ultra-Fast Choice"
            else: 
                item['note'] = "✅ Standard Option"

            item['score'] = round(score, 2)
            candidates.append(item)

    candidates.sort(key=lambda x: x['score'])
    top_5 = candidates[:5]

    final_results = []
    trip_polyline = None
    charger_stop_info = None
    
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

            charger_stop_info = {
                "lat": station["latitude"],
                "lng": station["longitude"],
                "name": station["name"]
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
            "polyline": trip_polyline 
        },
        "options": final_results
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 AI Service Running on Port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)