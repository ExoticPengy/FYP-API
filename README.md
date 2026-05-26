# FYP-API — EV Charging Station Recommendation Engine

A FastAPI microservice that recommends electric vehicle charging stops along a trip. Takes an origin and destination, scores nearby chargers by convenience, cost, and availability, and returns the best option with a predicted charging time from a trained ML model.

Final Year Project.

## How It Works

1. **Input** — Origin/destination coordinates, battery SoC, target SoC, battery capacity, and charger speed preference
2. **Search** — 3-tier algorithm finds reachable chargers near the route midpoint:
   - Standard: chargers near the midpoint filtered by speed preference
   - Emergency fallback: any reachable charger regardless of speed
   - Absolute closest: last resort, even if out of range
3. **ML Prediction** — A scikit-learn model predicts charging time from current SoC, target SoC, battery capacity, and charger power (falls back to physics formula if model unavailable)
4. **Scoring** — Stations ranked by: proximity to midpoint, availability, power output, and connector type
5. **Output** — Top 5 recommendations with route info from Google Maps Directions API

## API

```
POST /recommendations
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_lat` | float | required | Origin latitude |
| `start_lng` | float | required | Origin longitude |
| `end_lat` | float | required | Destination latitude |
| `end_lng` | float | required | Destination longitude |
| `current_soc` | int | 20 | Current battery charge (%) |
| `target_soc` | int | 80 | Desired battery charge (%) |
| `battery_capacity_kwh` | int | 60 | Battery size (kWh) |
| `preferred_speed` | str | "any" | `any`, `fast` (≥50kW), `ultrafast` (≥100kW) |

## Tech Stack

- **FastAPI** + **Uvicorn** — Async Python web framework
- **scikit-learn** — Charging time prediction model (`charge_model_final.pkl`)
- **SQLAlchemy** + **PostgreSQL** — Live charger database (`psycopg2-binary`)
- **Google Maps Directions API** — Route distance, duration, and polyline
- **Haversine formula** — Great-circle distance calculations

A simulated database (`simulated_db.py`) with 18 Malaysian charging stations is included for development without PostgreSQL.

## Setup

```bash
pip install -r requirements.txt
```

Set environment variables: `DB_HOST`, `DB_PORT`, `DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD` (or `DATABASE_URL`), and `GOOGLE_MAPS_API_KEY`.

```bash
uvicorn main:app --port 8001
```

CORS is open for all origins — configure before production use.
