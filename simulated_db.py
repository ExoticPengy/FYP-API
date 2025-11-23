# simulated_db.py

STATIONS_DB = {
    # ==========================================
    # CENTRAL REGION (Kuala Lumpur / Selangor)
    # ==========================================
    "st_001": {
        "id": "st_001",
        "name": "Pavilion KL (Tesla Supercharger)",
        "latitude": 3.1485,
        "longitude": 101.7131,
        "charger_type": "DC Fast",
        "charger_max_power": 250.0, 
        "status": "Available"
    },
    "st_002": {
        "id": "st_002",
        "name": "Suria KLCC (Premium)",
        "latitude": 3.1578,
        "longitude": 101.7117,
        "charger_type": "AC",
        "charger_max_power": 22.0, # Slow
        "status": "Busy"
    },
    "st_003": {
        "id": "st_003",
        "name": "Sunway Pyramid (Gentari)",
        "latitude": 3.0733,
        "longitude": 101.6078,
        "charger_type": "DC Fast",
        "charger_max_power": 60.0,
        "status": "Available"
    },
    "st_004": {
        "id": "st_004",
        "name": "IOI City Mall Putrajaya",
        "latitude": 2.9700,
        "longitude": 101.7144,
        "charger_type": "DC Fast",
        "charger_max_power": 50.0,
        "status": "Available"
    },

    # ==========================================
    # NORTHERN ROUTE (Perak - Midpoint to Penang)
    # ==========================================
    "st_005": {
        "id": "st_005",
        "name": "Shell Recharge Tapah R&R (Northbound)",
        "latitude": 4.2505, 
        "longitude": 101.3120,
        "charger_type": "DC Fast",
        "charger_max_power": 180.0, # Super fast
        "status": "Available"
    },
    "st_006": {
        "id": "st_006",
        "name": "Petronas Simpang Pulai (Ipoh South)",
        "latitude": 4.5667, 
        "longitude": 101.1235,
        "charger_type": "DC Fast",
        "charger_max_power": 50.0,
        "status": "Available"
    },
    "st_007": {
        "id": "st_007",
        "name": "XPark Sunway City Ipoh",
        "latitude": 4.6253, 
        "longitude": 101.1558,
        "charger_type": "DC Fast",
        "charger_max_power": 60.0,
        "status": "Charging" # Busy - AI should penalize this
    },
    "st_008": {
        "id": "st_008",
        "name": "Caltex Bukit Gantang R&R",
        "latitude": 4.7850,
        "longitude": 100.7780,
        "charger_type": "DC Fast",
        "charger_max_power": 50.0,
        "status": "Available"
    },
    "st_009": {
        "id": "st_009",
        "name": "Tesla Supercharger Maju Iskandar (Tapah)",
        "latitude": 4.2600,
        "longitude": 101.3000,
        "charger_type": "DC Fast",
        "charger_max_power": 250.0,
        "status": "Offline" # Broken - AI must ignore
    },

    # ==========================================
    # PENANG (Destination)
    # ==========================================
    "st_010": {
        "id": "st_010",
        "name": "Gurney Plaza Penang",
        "latitude": 5.4375, 
        "longitude": 100.3099,
        "charger_type": "DC Fast",
        "charger_max_power": 50.0,
        "status": "Available"
    },
    "st_011": {
        "id": "st_011",
        "name": "IKEA Batu Kawan (Mainland)",
        "latitude": 5.2333,
        "longitude": 100.4333,
        "charger_type": "DC Fast",
        "charger_max_power": 60.0,
        "status": "Available"
    },

    # ==========================================
    # SOUTHERN ROUTE (Seremban / Melaka / Johor)
    # ==========================================
    "st_012": {
        "id": "st_012",
        "name": "Shell R&R Seremban (Southbound)",
        "latitude": 2.7450,
        "longitude": 101.9000,
        "charger_type": "DC Fast",
        "charger_max_power": 180.0,
        "status": "Available"
    },
    "st_013": {
        "id": "st_013",
        "name": "Ayer Keroh R&R (Melaka)",
        "latitude": 2.3900,
        "longitude": 102.1900,
        "charger_type": "DC Fast",
        "charger_max_power": 50.0,
        "status": "Charging"
    },
    "st_014": {
        "id": "st_014",
        "name": "Shell Recharge Tangkak",
        "latitude": 2.2533,
        "longitude": 102.5333,
        "charger_type": "DC Fast",
        "charger_max_power": 180.0,
        "status": "Available"
    },
    "st_015": {
        "id": "st_015",
        "name": "Skudai R&R (Johor)",
        "latitude": 1.6300,
        "longitude": 103.6300,
        "charger_type": "DC Fast",
        "charger_max_power": 120.0,
        "status": "Available"
    },
    "st_016": {
        "id": "st_016",
        "name": "Mid Valley Southkey JB",
        "latitude": 1.5000,
        "longitude": 103.7700,
        "charger_type": "AC",
        "charger_max_power": 11.0,
        "status": "Available"
    },

    # ==========================================
    # EAST COAST (Genting / Pahang)
    # ==========================================
    "st_017": {
        "id": "st_017",
        "name": "Genting Highlands Premium Outlets",
        "latitude": 3.4030,
        "longitude": 101.7820,
        "charger_type": "DC Fast",
        "charger_max_power": 120.0,
        "status": "Available"
    },
    "st_018": {
        "id": "st_018",
        "name": "Kuantan City Mall",
        "latitude": 3.8167,
        "longitude": 103.3333,
        "charger_type": "DC Fast",
        "charger_max_power": 60.0,
        "status": "Available"
    }
}