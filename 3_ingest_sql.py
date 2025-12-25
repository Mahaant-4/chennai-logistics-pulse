import mysql.connector
import osmnx as ox
import h3
from shapely.geometry import Point, Polygon

# --- CONFIGURATION ---
DB_CONFIG = {
    'user': 'root',
    'password': 'rootpassword123',
    'host': '127.0.0.1', # Localhost
    'port': 3307,        # The port we mapped in Docker
    'database': 'chennai_logistics'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def create_tables(cursor):
    print("🛠 Creating Tables...")
    
    # 1. Hexagon Table
    # SRID 4326 is the standard ID for "GPS Coordinates on Earth"
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS city_hexagons (
            hex_id VARCHAR(16) PRIMARY KEY,
            geometry POLYGON NOT NULL SRID 4326
        )
    """)
    
    # 2. Road Nodes Table (Intersections)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS road_nodes (
            node_id BIGINT PRIMARY KEY,
            geometry POINT NOT NULL SRID 4326
        )
    """)
    print("✅ Tables ready.")

def generate_hex_data():
    """ Re-runs our hex generation logic to get the data for insertion """
    print("⬡ Generating Hexagons for DB...")
    gdf = ox.geocode_to_gdf("Chennai, India")
    city_polygon = gdf.geometry.iloc[0]
    centroid = city_polygon.centroid
    
    # Generate Disk
    center_h3 = h3.latlng_to_cell(centroid.y, centroid.x, 8)
    candidate_hexes = h3.grid_disk(center_h3, 60)
    
    hex_data = []
    for hex_id in candidate_hexes:
        lat, lon = h3.cell_to_latlng(hex_id)
        if city_polygon.contains(Point(lon, lat)):
            # Convert to WKT format: POLYGON((lon lat, lon lat...))
            # 1. Get boundary
            boundary = h3.cell_to_boundary(hex_id) # ((lat, lon), ...)
            
            # 2. Format as String string for SQL: "lon lat, lon lat"
            # Note: We must close the loop (repeat start point at end) for valid WKT
            coords_str = ", ".join([f"{lon} {lat}" for lat, lon in boundary])
            
            # Add first point again to close the loop
            first_lat, first_lon = boundary[0]
            coords_str += f", {first_lon} {first_lat}"
            
            wkt_string = f"POLYGON(({coords_str}))"
            hex_data.append((hex_id, wkt_string))
            
    return hex_data

def insert_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    create_tables(cursor)
    
    # --- INSERT HEXAGONS ---
    hex_data = generate_hex_data()
    print(f"🚀 Inserting {len(hex_data)} hexagons into MySQL...")
    
    # We use 'axis-order=long-lat' to force MySQL to understand our Lon-Lat input
    insert_hex_query = """
        INSERT IGNORE INTO city_hexagons (hex_id, geometry) 
        VALUES (%s, ST_GeomFromText(%s, 4326, 'axis-order=long-lat'))
    """
    
    # executemany is 100x faster than a loop
    cursor.executemany(insert_hex_query, hex_data)
    conn.commit()
    print("✅ Hexagons inserted!")

    # --- INSERT ROAD NODES (SAMPLE) ---
    print("🛣 Downloading Road Network for Nodes...")
    # Using 'simplify=True' to keep it light
    G = ox.graph_from_place("Chennai, India", network_type='drive', simplify=True)
    
    node_data = []
    for node_id, data in G.nodes(data=True):
        # WKT for Point: "POINT(lon lat)"
        wkt_point = f"POINT({data['x']} {data['y']})"
        node_data.append((node_id, wkt_point))
    
    print(f"🚀 Inserting {len(node_data)} road nodes...")
    
    insert_node_query = """
        INSERT IGNORE INTO road_nodes (node_id, geometry) 
        VALUES (%s, ST_GeomFromText(%s, 4326, 'axis-order=long-lat'))
    """
    
    # Doing it in chunks to be safe
    batch_size = 5000
    for i in range(0, len(node_data), batch_size):
        batch = node_data[i:i+batch_size]
        cursor.executemany(insert_node_query, batch)
        conn.commit()
        print(f"   Saved batch {i}...")

    print("🎉 Database Ingestion Complete!")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    insert_data()