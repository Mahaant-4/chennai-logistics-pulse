import mysql.connector
import osmnx as ox
import geopandas as gpd
import pandas as pd
from shapely import wkt

# --- CONFIG ---
DB_CONFIG = {
    'user': 'root',
    'password': 'rootpassword123',
    'host': '127.0.0.1',
    'port': 3307,
    'database': 'chennai_logistics'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def calc_static_features():
    print("🛣 Downloading Chennai Road Network (for calculation)...")
    G = ox.graph_from_place("Chennai, India", network_type='drive', simplify=True)
    gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)
    
    print(f"   Loaded {len(gdf_nodes)} nodes and {len(gdf_edges)} road segments.")

    print("📥 Fetching Hexagons from MySQL...")
    conn = get_db_connection()
    
    # --- THE FIX IS HERE ---
    # We add 'axis-order=long-lat' to ST_AsText so MySQL gives us (Lon, Lat)
    sql = "SELECT hex_id, ST_AsText(geometry, 'axis-order=long-lat') as geom FROM city_hexagons"
    
    df_hex = pd.read_sql(sql, conn)
    
    # Convert text to shapes
    df_hex['geometry'] = df_hex['geom'].apply(wkt.loads)
    gdf_hex = gpd.GeoDataFrame(df_hex, geometry='geometry', crs="EPSG:4326")
    
    print("🧮 Performing Spatial Join (Bucketing)...")
    
    # 1. Count Nodes
    nodes_in_hex = gpd.sjoin(gdf_nodes, gdf_hex, how="inner", predicate="within")
    node_counts = nodes_in_hex.groupby("hex_id").size()
    print(f"   Matches found: {len(nodes_in_hex)} nodes fell into hexagons.")
    
    # 2. Calculate Road Length
    gdf_edges['centroid'] = gdf_edges.geometry.centroid
    gdf_edges_centroid = gdf_edges.set_geometry('centroid')
    
    roads_in_hex = gpd.sjoin(gdf_edges_centroid, gdf_hex, how="inner", predicate="within")
    road_lengths = roads_in_hex.groupby("hex_id")['length'].sum()

    print(f"💾 Updating Database for {len(gdf_hex)} hexagons...")
    
    cursor = conn.cursor()
    update_query = """
        UPDATE city_hexagons 
        SET node_count = %s, road_length_meters = %s 
        WHERE hex_id = %s
    """
    
    updates = []
    for hex_id in gdf_hex['hex_id']:
        n_count = int(node_counts.get(hex_id, 0))
        r_len = float(road_lengths.get(hex_id, 0.0))
        
        # Only print a sample if it's non-zero (for debugging)
        if n_count > 0 and len(updates) < 3:
            print(f"   Sample Update -> Hex: {hex_id}, Nodes: {n_count}")
            
        updates.append((n_count, r_len, hex_id))
        
    cursor.executemany(update_query, updates)
    conn.commit()
    
    print("✅ Success! Feature Engineering complete.")
    conn.close()

if __name__ == "__main__":
    calc_static_features()