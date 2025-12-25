import mysql.connector
from shapely import wkt
import numpy as np

# Database Config
DB_CONFIG = {
    'user': 'root', 'password': 'rootpassword123',
    'host': '127.0.0.1', 'port': 3307, 'database': 'chennai_logistics'
}

# --- FULL LANDMARK LIST (40+ Locations) ---
LANDMARKS = {
    # NORTH
    "Chennai Port": (13.0950, 80.2900),
    "Royapuram": (13.1137, 80.2954),
    "Tiruvottiyur": (13.1600, 80.3000),
    "Washermanpet": (13.1067, 80.2754),
    "Perambur": (13.1110, 80.2320),
    "Kolathur": (13.1240, 80.2120),
    "Villivakkam": (13.1060, 80.2030),
    "Madhavaram": (13.1400, 80.2300),
    
    # CENTRAL
    "Anna Nagar": (13.0850, 80.2100),
    "Mogappair": (13.0830, 80.1740),
    "Koyambedu": (13.0694, 80.1948),
    "Vadapalani": (13.0520, 80.2110),
    "T. Nagar": (13.0418, 80.2341),
    "Nungambakkam": (13.0569, 80.2425),
    "Egmore": (13.0732, 80.2609),
    "Triplicane": (13.0587, 80.2736),
    "Mylapore": (13.0368, 80.2676),
    "Alwarpet": (13.0330, 80.2530),
    "Ashok Nagar": (13.0370, 80.2120),
    "K.K. Nagar": (13.0410, 80.1990),
    
    # SOUTH
    "Adyar": (13.0012, 80.2565),
    "Besant Nagar": (13.0003, 80.2667),
    "Thiruvanmiyur": (12.9830, 80.2594),
    "Velachery": (12.9750, 80.2207),
    "Guindy": (13.0067, 80.2206),
    "Saidapet": (13.0213, 80.2231),
    "Pallavaram": (12.9675, 80.1491),
    "Chromepet": (12.9516, 80.1407),
    "Tambaram": (12.9249, 80.1000),
    "Airport": (12.9800, 80.1650),
    
    # WEST
    "Ambattur": (13.1143, 80.1548),
    "Porur": (13.0382, 80.1565),
    "Poonamallee": (13.0500, 80.1100),
    "Maduravoyal": (13.0600, 80.1700),
    
    # OMR / IT CORRIDOR
    "Perungudi": (12.9600, 80.2450),
    "Sholinganallur": (12.9010, 80.2279),
    "Navallur": (12.8440, 80.2230),
    "Siruseri": (12.8220, 80.2190)
}

def fix_names():
    print("🔌 Connecting to DB...")
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("SELECT hex_id, ST_AsText(geometry) FROM city_hexagons")
    rows = cursor.fetchall()
    
    print(f"🗺️ Mapping {len(rows)} hexagons to {len(LANDMARKS)} neighborhoods...")
    
    updates = []
    
    for row in rows:
        h_id, wkt_geom = row
        try:
            if isinstance(wkt_geom, bytes): wkt_geom = wkt_geom.decode('utf-8')
            poly = wkt.loads(wkt_geom)
            center = poly.centroid
            
            # Determine correct Lat/Lon
            val1, val2 = center.x, center.y
            if 12.0 < val2 < 14.0:
                hex_lat, hex_lon = center.y, center.x
            else:
                hex_lat, hex_lon = center.x, center.y

            # Find closest landmark
            min_dist = float('inf')
            best_name = "Unknown"
            
            for name, (l_lat, l_lon) in LANDMARKS.items():
                dist = np.sqrt((hex_lat - l_lat)**2 + (hex_lon - l_lon)**2)
                if dist < min_dist:
                    min_dist = dist
                    best_name = name
            
            updates.append((best_name, h_id))
        except:
            continue

    print(f"💾 Updating MySQL...")
    query = "UPDATE city_hexagons SET place_name = %s WHERE hex_id = %s"
    
    batch_size = 100
    for i in range(0, len(updates), batch_size):
        cursor.executemany(query, updates[i:i+batch_size])
        conn.commit()
        
    print("✅ Full Neighborhood Map Applied!")
    conn.close()

if __name__ == "__main__":
    fix_names()