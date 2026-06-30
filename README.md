<h1 align="center">⚡ FYP API</h1>
<h3 align="center"><em>Where should an EV stop to charge — and how long will it take? Ask the API.</em></h3>

<p align="center">
  <img src="https://img.shields.io/badge/language-Python-3776AB?style=for-the-badge&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/framework-FastAPI-009688?style=for-the-badge&logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/ML-scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn" alt="scikit-learn"/>
  <img src="https://img.shields.io/badge/database-PostgreSQL-4169E1?style=for-the-badge&logo=postgresql" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/maps-Google%20Maps-4285F4?style=for-the-badge&logo=googlemaps" alt="Google Maps"/>
</p>

---

## 📖 About The Project

Long EV trips come with a question gas cars never had: *will I make it, and where should I plug in?* **FYP API** answers it. Give it your start and destination, your battery's current and target charge, and it returns the best charging stops along the way — ranked by how little they detour you, what they'll cost, and how long you'll be waiting.

The clever part is the charging-time estimate: instead of guessing, a **trained scikit-learn model** predicts how many minutes each stop will actually take for *your* battery and *that* charger's speed. The service is built with **FastAPI**, reads from a live **PostgreSQL** charger database, and pulls real routes from the **Google Maps Directions API**.

> 🎓 Built as a Final Year Project.

---

## ✨ Features

|  | Feature | Description |
|--|---------|-------------|
| 🔌 | **Smart Charger Search** | A 3-tier algorithm finds the best reachable charger near your route. |
| 🤖 | **ML Charging-Time Prediction** | A trained model estimates charging duration per stop and battery. |
| 🧮 | **Physics Fallback** | If the model is unavailable, falls back to an energy/power formula. |
| 💰 | **Cost Estimation** | Estimates charging cost in MYR based on connector type and power. |
| 🗺️ | **Real Route Data** | Pulls distance, duration, and polyline from Google Maps. |
| 📍 | **Range-Aware** | Filters chargers by your battery's safe driveable range. |
| 🏆 | **Top-5 Ranking** | Returns the five best options, scored by detour, availability, and power. |
| 🧪 | **Built-in Simulated DB** | 18 Malaysian stations bundled for development without PostgreSQL. |

---

## 🧭 How It Works

```
   ┌────────────────────────────────────────────┐
   │  REQUEST: origin, destination, SoC, target, │
   │           battery size, speed preference    │
   └─────────────────────┬──────────────────────┘
                         ▼
          ┌──────────────────────────────┐
          │   TIER 1 · Standard           │
          │   Chargers near midpoint,     │
          │   matching speed preference   │
          └──────────────┬───────────────┘
                  (none found?)
                         ▼
          ┌──────────────────────────────┐
          │   TIER 2 · Emergency          │
          │   Any reachable charger,      │
          │   ignoring speed preference   │
          └──────────────┬───────────────┘
                  (still none?)
                         ▼
          ┌──────────────────────────────┐
          │   TIER 3 · Last Resort        │
          │   Absolute closest charger,   │
          │   even if out of range        │
          └──────────────┬───────────────┘
                         ▼
   ┌────────────────────────────────────────────┐
   │  ML predicts time · estimate cost · score   │
   │  rank · Google Maps route for top pick      │
   └─────────────────────┬──────────────────────┘
                         ▼
              RESPONSE: top 5 options + trip
```

---

## 🔌 API

```http
POST /recommendations
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_lat` | float | *required* | Origin latitude |
| `start_lng` | float | *required* | Origin longitude |
| `end_lat` | float | *required* | Destination latitude |
| `end_lng` | float | *required* | Destination longitude |
| `current_soc` | int | `20` | Current battery charge (%) |
| `target_soc` | int | `80` | Desired battery charge (%) |
| `battery_capacity_kwh` | int | `60` | Battery size (kWh) |
| `preferred_speed` | str | `"any"` | `any`, `fast` (≥50 kW), `ultrafast` (≥100 kW) |

Returns the trip summary (route polyline, distance, duration, safe range) and up to **5 ranked charging options**, each with detour, predicted time, estimated cost, status, and a Google Maps directions link.

---

## 🛠️ Technology Stack

| Category | Technology | Purpose |
|:---------|:-----------|:--------|
| **Framework** | FastAPI + Uvicorn | Async Python web framework |
| **ML** | scikit-learn (`charge_model_final.pkl`) | Charging-time prediction (via `joblib`) |
| **Data** | pandas | Feature framing for the model |
| **Database** | PostgreSQL + SQLAlchemy (`psycopg2-binary`) | Live charger data |
| **Routing** | Google Maps Directions API (`httpx`, `polyline`) | Real route distance, duration, polyline |
| **Geometry** | Haversine formula | Great-circle distance calculations |
| **Config** | python-dotenv | Environment variable loading |

---

## 📂 Project Structure

```
FYP-API/
├── main.py                  # FastAPI app + recommendation endpoint
├── database.py              # Live charger DB access
├── simulated_db.py          # 18 bundled Malaysian stations (dev fallback)
├── test_db.py               # Database tests
├── charge_model_final.pkl   # Trained scikit-learn model
└── requirements.txt         # Python dependencies
```

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.10+
- **PostgreSQL** (optional — a simulated DB is bundled)
- A **Google Maps** API key (optional — falls back to a straight-line estimate)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/ExoticPengy/FYP-API.git
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure** — set environment variables: `DB_HOST`, `DB_PORT`, `DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD` (or `DATABASE_URL`), and `GOOGLE_MAPS_API_KEY`.

4. **Run the server**

   ```bash
   uvicorn main:app --port 8001
   ```

   Interactive docs at `http://localhost:8001/docs`.

> ⚠️ CORS is open to all origins for development — lock it down before production.

---

## 📝 License

Academic project — all rights reserved.
