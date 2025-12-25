import mysql.connector
import geopandas as gpd
import pandas as pd
from shapely import wkt
from shapely.geometry import Point

# --- CONFIG ---
DB_CONFIG = {
    'user': 'root',
    'password': 'rootpassword123',
    'host': '127.0.0.1',
    'port': 3307,
    'database': 'chennai_logistics'
}

# Known Flood Hotspots in Chennai (Lat, Lon)
# We are manually defining these based on historical 2015/2023 flood data
FLOOD_HOTSPOTS = {
    "Velachery": (12.9806, 80.2166),
    "Madipakkam": (12.9647, 80.1961),
    "Adyar River Bank": (13.0065, 80.2565),
    "Chembarambakkam Flow Path": (13.0183, 80.1650),
    "T. Nagar (Usman Road)": (13.0418, 80.2341)
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def tag_flood_zones():
    print("🌊 Loading Hexagons from DB...")
    conn = get_db_connection()
    # Remember: Force MySQL to give us Longitude-Latitude order!
    sql = "SELECT hex_id, ST_AsText(geometry, 'axis-order=long-lat') as geom FROM city_hexagons"
    df_hex = pd.read_sql(sql, conn)
    
    # Convert to GeoDataFrame
    df_hex['geometry'] = df_hex['geom'].apply(wkt.loads)
    gdf_hex = gpd.GeoDataFrame(df_hex, geometry='geometry', crs="EPSG:4326")

    print("⚠️ Creating Flood Risk Zones (1km Buffers)...")
    
    risk_shapes = []
    for name, coords in FLOOD_HOTSPOTS.items():
        lat, lon = coords
        # Create a point
        p = Point(lon, lat) # Shapely needs (Lon, Lat)
        
        # Buffer it. 
        # Note: In EPSG:4326 (Degrees), 1 degree ~= 111km. 
        # So 0.01 degrees is roughly 1km.
        risk_zone = p.buffer(0.01) 
        risk_shapes.append(risk_zone)
        
    # Combine all circles into one "Mega Danger Zone"
    risk_union = gpd.GeoSeries(risk_shapes).unary_union
    
    print("🧮 Checking which hexagons intersect Flood Zones...")
    
    # Check intersection
    # .intersects returns True/False for each hexagon
    gdf_hex['is_flood_prone'] = gdf_hex.geometry.intersects(risk_union).astype(int)
    
    # Count how many are risky
    risky_count = gdf_hex['is_flood_prone'].sum()
    print(f"   Found {risky_count} hexagons in flood-prone areas.")

    print("💾 Updating Database...")
    cursor = conn.cursor()
    
    update_query = "UPDATE city_hexagons SET is_flood_prone = %s WHERE hex_id = %s"
    
    updates = []
    # Filter only the risky ones to save time
    risky_df = gdf_hex[gdf_hex['is_flood_prone'] == 1]
    
    for hex_id in risky_df['hex_id']:
        updates.append((1, hex_id))
        
    cursor.executemany(update_query, updates)
    conn.commit()
    
    print("✅ Flood Layer Integrated.")
    conn.close()

if __name__ == "__main__":
    tag_flood_zones()