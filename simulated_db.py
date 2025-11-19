# simulated_db.py

# This is our fake database of all the charging stations in our network
STATIONS_DB = {
    "st_001": {
        "name": "Pavilion KL (DC Fast)",
        "latitude": 3.1485,
        "longitude": 101.7131,
        "charger_type": "DC Fast Charger",
        "charger_max_power": 150.0,
        "available_chargers": 2
    },
    "st_002": {
        "name": "Suria KLCC (Level 2)",
        "latitude": 3.1578,
        "longitude": 101.7117,
        "charger_type": "Level 2",
        "charger_max_power": 7.0,
        "available_chargers": 0 
    },
    "st_003": {
        "name": "Mid Valley Megamall (DC Fast)",
        "latitude": 3.1186,
        "longitude": 101.6773,
        "charger_type": "DC Fast Charger",
        "charger_max_power": 120.0, 
        "available_chargers": 4
    },
    "st_004": {
        "name": "TAR UMT (Level 2)",
        "latitude": 3.2139,
        "longitude": 101.7280,
        "charger_type": "Level 2",
        "charger_max_power": 7.0,
        "available_chargers": 5
    }
}

def get_all_stations():
    return list(STATIONS_DB.values())

def get_station_by_id(station_id):
    return STATIONS_DB.get(station_id)