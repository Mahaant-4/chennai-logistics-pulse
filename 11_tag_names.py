import mysql.connector
import pandas as pd
import h3
from shapely import wkt
from shapely.geometry import Point
import numpy as np

# --- CONFIG ---
DB_CONFIG = {
    'user': 'root',
    'password': 'rootpassword123',
    'host': '127.0.0.1',
    'port': 3307,
    'database': 'chennai_logistics'
}

# Major Anchor Points in Chennai
LANDMARKS = {
    "George Town": (13.096, 80.287),
    "Central Station": (13.082, 80.275),
    "Egmore": (13.073, 80.261),
    "Marina Beach": (13.055, 80.283),
    "Mylapore": (13.033, 80.267),
    "T. Nagar": (13.041, 80.233),
    "Kodambakkam": (13.052, 80.225),
    "Nungambakkam": (13.062, 80.240),
    "Anna Nagar": (13.085, 80.210),
    "Kilpauk": (13.082, 80.243),
    "Adyar": (13.006, 80.257),
    "Besant Nagar": (12.997, 80.272),
    "Thiruvanmiyur": (12.983, 80.263),
    "Velachery": (12.980, 80.220),
    "Guindy": (13.010, 80.212),
    "Saidapet": (13.021, 80.223),
    "Vadapalani": (13.050, 80.212),
    "Koyambedu": (13.069, 80.194),
    "Ashok Nagar": (13.037, 80.215),
    "Ekkatuthangal": (13.022, 80.204),
    "Madipakkam": (12.964, 80.196),
    "Porur": (13.034, 80.157),
    "Mount Road": (13.065, 80.267),
    "Royapettah": (13.054, 80.264),
    "Alwarpet": (13.033, 80.252)
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def tag_places():
    print("📥 Loading Hexagons...")
    conn = get_db_connection()
    # Get ID and Geometry
    sql = "SELECT hex_id, ST_AsText(geometry, 'axis-order=long-lat') as geom FROM city_hexagons"
    df = pd.read_sql(sql, conn)
    
    # We need the CENTER of each hexagon
    # H3 function 'cell_to_latlng' returns (Lat, Lon)
    df['lat'] = df['hex_id'].apply(lambda x: h3.cell_to_latlng(x)[0])
    df['lon'] = df['hex_id'].apply(lambda x: h3.cell_to_latlng(x)[1])
    
    print("🏷️ Tagging Neighborhoods...")
    
    updates = []
    
    for index, row in df.iterrows():
        hex_lat = row['lat']
        hex_lon = row['lon']
        
        # Find closest landmark
        min_dist = float('inf')
        best_name = "Chennai City"
        
        for name, (l_lat, l_lon) in LANDMARKS.items():
            # Simple Euclidean distance (Good enough for tagging nearby zones)
            # dist = sqrt((x2-x1)^2 + (y2-y1)^2)
            dist = np.sqrt((hex_lat - l_lat)**2 + (hex_lon - l_lon)**2)
            
            if dist < min_dist:
                min_dist = dist
                best_name = name
        
        # Add "Near" if it's not super close, just for flavor
        updates.append((best_name, row['hex_id']))

    print(f"💾 Saving {len(updates)} names to database...")
    
    cursor = conn.cursor()
    update_query = "UPDATE city_hexagons SET place_name = %s WHERE hex_id = %s"
    cursor.executemany(update_query, updates)
    conn.commit()
    
    print("✅ Done! Map is now human-readable.")
    conn.close()

if __name__ == "__main__":
    tag_places()