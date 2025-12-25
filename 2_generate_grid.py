import osmnx as ox
import h3
import geopandas as gpd
from shapely.geometry import Point, Polygon
import matplotlib.pyplot as plt

def generate_hex_grid():
    print("📍 Fetching Chennai city boundary...")
    gdf = ox.geocode_to_gdf("Chennai, India")
    city_polygon = gdf.geometry.iloc[0]
    
    print("🔍 Calculating Centroid for Radial Scan...")
    centroid = city_polygon.centroid
    center_lat = centroid.y
    center_lon = centroid.x
    
    # Generate candidate grid
    center_h3 = h3.latlng_to_cell(center_lat, center_lon, 8)
    candidate_hexes = h3.grid_disk(center_h3, 60)
    
    # Filter for hexagons inside Chennai
    final_hexes = []
    for hex_id in candidate_hexes:
        lat, lon = h3.cell_to_latlng(hex_id)
        if city_polygon.contains(Point(lon, lat)):
            final_hexes.append(hex_id)
            
    print(f"✅ Filter complete! Found {len(final_hexes)} hexagons inside Chennai.")

    # --- PLOTTING SECTION (FIXED) ---
    print("🎨 Plotting the grid...")
    
    hex_polygons = []
    for hex_id in final_hexes:
        # H3 v4 Function: cell_to_boundary
        # Returns a tuple of coordinates: ((lat, lon), (lat, lon), ...)
        boundary_coords = h3.cell_to_boundary(hex_id)
        
        # Swap (Lat, Lon) -> (Lon, Lat) for plotting
        reversed_coords = [(lon, lat) for lat, lon in boundary_coords]
        
        hex_polygons.append(Polygon(reversed_coords))
        
    hex_gdf = gpd.GeoDataFrame(geometry=hex_polygons, crs="EPSG:4326")
    
    # Plotting
    fig, ax = plt.subplots(figsize=(10, 10))
    gdf.plot(ax=ax, facecolor="none", edgecolor="red", linewidth=2, zorder=2)
    hex_gdf.plot(ax=ax, facecolor="blue", alpha=0.3, edgecolor="white", zorder=1)
    
    plt.title(f"Chennai H3 Grid (Res 8) - {len(final_hexes)} Hexagons")
    plt.show()

if __name__ == "__main__":
    generate_hex_grid()