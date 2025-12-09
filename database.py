# database.py
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# 1. Setup Database Connection
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_DATABASE", "evcms_db")
    DB_USER = os.getenv("DB_USERNAME", "postgres")
    DB_PASS = os.getenv("DB_PASSWORD", "root")
    
    # Construct URL for local dev
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Fix for Render/Cloud URLs that use 'postgres://' instead of 'postgresql://'
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

try:
    engine = create_engine(DATABASE_URL)
    print("✅ Database Engine Configured.")
except Exception as e:
    print(f"❌ DB Config Error: {e}")

def get_live_chargers():
    try:
        with engine.connect() as conn:
            # JOIN query to get Station Location + Charger Power & Status
            query = text("""
                SELECT 
                    c.id as charger_id,
                    s.name as station_name,
                    s.latitude, 
                    s.longitude,
                    c.status,
                    c.power_output as charger_max_power,
                    c.connector_type as charger_type,
                    c.fee as cost_per_kwh
                FROM chargers c
                JOIN stations s ON c.station_id = s.id
                WHERE s.latitude IS NOT NULL AND s.longitude IS NOT NULL
            """)
            
            result = conn.execute(query)
            
            chargers_db = {}
            for row in result:
                unique_id = f"st_{row.charger_id}"
                chargers_db[unique_id] = {
                    "id": unique_id,
                    "name": row.station_name,
                    "latitude": float(row.latitude),
                    "longitude": float(row.longitude),
                    "status": row.status.capitalize() if row.status else "Unknown", 
                    "charger_max_power": float(row.charger_max_power or 50.0),
                    "charger_type": row.charger_type or "DC Fast",
                    "cost_per_kwh": float(row.cost_per_kwh or 1.00)
                }
            
            print(f"✅ Loaded {len(chargers_db)} live chargers from PostgreSQL.")
            return chargers_db

    except Exception as e:
        print(f"❌ Database Query Error: {e}")
        return {}