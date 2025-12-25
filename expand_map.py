import mysql.connector
import h3
import random
import math

# --- CONFIG ---
DB_CONFIG = {
    'user': 'root', 'password': 'rootpassword123',
    'host': '127.0.0.1', 'port': 3307, 'database': 'chennai_logistics'
}

# --- REAL CHENNAI NEIGHBORHOODS ---
CHENNAI_AREAS = [
    # North
    {"name": "Ennore", "lat": 13.20, "lon": 80.32},
    {"name": "Manali", "lat": 13.16, "lon": 80.26},
    {"name": "Tiruvottiyur", "lat": 13.16, "lon": 80.30},
    {"name": "Tondiarpet", "lat": 13.12, "lon": 80.28},
    {"name": "Royapuram", "lat": 13.11, "lon": 80.29},
    {"name": "Madhavaram", "lat": 13.14, "lon": 80.23},
    {"name": "Red Hills", "lat": 13.15, "lon": 80.19},
    
    # West
    {"name": "Ambattur", "lat": 13.11, "lon": 80.15},
    {"name": "Avadi", "lat": 13.10, "lon": 80.10},
    {"name": "Mogappair", "lat": 13.08, "lon": 80.17},
    {"name": "Anna Nagar", "lat": 13.08, "lon": 80.21},
    {"name": "Koyambedu", "lat": 13.06, "lon": 80.20},
    {"name": "Maduravoyal", "lat": 13.06, "lon": 80.16},
    {"name": "Porur", "lat": 13.03, "lon": 80.15},
    {"name": "Poonamallee", "lat": 13.05, "lon": 80.09},
    
    # Central
    {"name": "Kilpauk", "lat": 13.08, "lon": 80.24},
    {"name": "Egmore", "lat": 13.07, "lon": 80.26},
    {"name": "Nungambakkam", "lat": 13.06, "lon": 80.24},
    {"name": "T. Nagar", "lat": 13.04, "lon": 80.23},
    {"name": "Kodambakkam", "lat": 13.05, "lon": 80.22},
    {"name": "Vadapalani", "lat": 13.05, "lon": 80.21},
    {"name": "Mylapore", "lat": 13.03, "lon": 80.26},
    {"name": "Triplicane", "lat": 13.05, "lon": 80.27},
    {"name": "Royapettah", "lat": 13.05, "lon": 80.26},
    
    # South
    {"name": "Saidapet", "lat": 13.02, "lon": 80.22},
    {"name": "Guindy", "lat": 13.00, "lon": 80.22},
    {"name": "Adyar", "lat": 13.00, "lon": 80.25},
    {"name": "Besant Nagar", "lat": 13.00, "lon": 80.27},
    {"name": "Thiruvanmiyur", "lat": 12.98, "lon": 80.26},
    {"name": "Velachery", "lat": 12.97, "lon": 80.22},
    
    # Suburbs & OMR
    {"name": "Pallavaram", "lat": 12.96, "lon": 80.14},
    {"name": "Chromepet", "lat": 12.95, "lon": 80.14},
    {"name": "Tambaram", "lat": 12.92, "lon": 80.12},
    {"name": "Perungalathur", "lat": 12.90, "lon": 80.09},
    {"name": "Vandalur", "lat": 12.89, "lon": 80.08},
    {"name": "Perungudi", "lat": 12.96, "lon": 80.24},
    {"name": "Thoraipakkam", "lat": 12.94, "lon": 80.23},
    {"name": "Sholinganallur", "lat": 12.90, "lon": 80.22},
    {"name": "Navalur", "lat": 12.86, "lon": 80.22},
    {"name": "Siruseri", "lat": 12.83, "lon": 80.22},
]

# --- EXACT SHAPE OF GREATER CHENNAI ---
CHENNAI_POLYGON = [
    (13.2400, 80.3300), (13.1900, 80.3000), (13.1600, 80.1800), 
    (13.1000, 80.1300), (13.0500, 80.0800), 
    (12.9500, 80.1000), (12.8800, 80.0700), 
    (12.8300, 80.1600), (12.8000, 80.2100), 
    (12.8200, 80.2400), (12.9000, 80.2500), 
    (12.9800, 80.2700), (13.0400, 80.2800), (13.1000, 80.3000), (13.2400, 80.3300)
]

def is_inside_chennai(lat, lon):
    n = len(CHENNAI_POLYGON)
    inside = False
    p1x, p1y = CHENNAI_POLYGON[0]
    for i in range(n + 1):
        p2x, p2y = CHENNAI_POLYGON[i % n]
        if lon > min(p1y, p2y):
            if lon <= max(p1y, p2y):
                if lat <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (lon - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or lat <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

# --- NEAREST NEIGHBOR LOGIC ---
def get_nearest_neighborhood(lat, lon):
    closest_name = "Unknown"
    min_dist = float('inf')
    
    for area in CHENNAI_AREAS:
        # Simple Euclidean distance is fine for this scale
        dist = math.sqrt((lat - area['lat'])**2 + (lon - area['lon'])**2)
        if dist < min_dist:
            min_dist = dist
            closest_name = area['name']
    
    return closest_name

def recreate_database():
    print("🌍 Connecting to Database...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # 1. Clear Old Data
    print("🧹 Wiping old map...")
    cursor.execute("DROP TABLE IF EXISTS city_hexagons")
    cursor.execute("""
        CREATE TABLE city_hexagons (
            hex_id VARCHAR(20) PRIMARY KEY,
            latitude FLOAT, longitude FLOAT,
            place_name VARCHAR(100), node_count INT,
            road_length_meters FLOAT, is_flood_prone TINYINT
        )
    """)
    
    # 2. SCANNING GRID (Resolution 7 - MASSIVE HEXAGONS)
    RESOLUTION = 8
    print(f"⬡ Scanning Big Grid (Res {RESOLUTION})...")
    
    hex_ids = set()
    step = 0.005
    
    lat = 12.80
    while lat < 13.25:
        lon = 80.00
        while lon < 80.35:
            if is_inside_chennai(lat, lon):
                try:
                    try: h_id = h3.latlng_to_cell(lat, lon, RESOLUTION)
                    except: h_id = h3.geo_to_h3(lat, lon, RESOLUTION)
                    hex_ids.add(h_id)
                except: pass
            lon += step
        lat += step
        
    print(f"✅ Generated {len(hex_ids)} Massive Hexagons!")

    # 3. Prepare Data
    data_to_insert = []
    print("📝 Preparing data rows with REAL NAMES...")
    
    for hex_id in hex_ids:
        try: lat, lon = h3.cell_to_latlng(hex_id)
        except: lat, lon = h3.h3_to_geo(hex_id)
        
        # --- NEW NAMING LOGIC ---
        place = get_nearest_neighborhood(lat, lon)
        
        nodes = random.randint(100, 500) 
        roads = random.randint(10000, 50000)
        flood = 1 if (13.00 < lat < 13.02 or 13.07 < lat < 13.09) and random.random() > 0.6 else 0
            
        data_to_insert.append((hex_id, lat, lon, place, nodes, roads, flood))

    # 4. Bulk Insert
    print("🚀 Uploading to Database...")
    sql = "INSERT INTO city_hexagons VALUES (%s, %s, %s, %s, %s, %s, %s)"
    batch_size = 1000
    for i in range(0, len(data_to_insert), batch_size):
        batch = data_to_insert[i:i+batch_size]
        cursor.executemany(sql, batch)
        conn.commit()

    cursor.close(); conn.close()
    print("✨ SUCCESS! Real-Name Map Created.")

if __name__ == "__main__":
    recreate_database()