import mysql.connector
import pandas as pd
import numpy as np
import random

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

def generate_synthetic_data():
    print("📥 Loading Data from MySQL...")
    conn = get_db_connection()
    
    # 1. Get Hexagons (The Location Context)
    query_hex = "SELECT hex_id, node_count, road_length_meters, is_flood_prone FROM city_hexagons"
    df_hex = pd.read_sql(query_hex, conn)
    
    # 2. Get Weather (The Environmental Context)
    query_weather = "SELECT log_date, rainfall_mm, max_temp_c FROM weather_history"
    df_weather = pd.read_sql(query_weather, conn)
    
    conn.close()
    
    print(f"   Loaded {len(df_hex)} hexagons and {len(df_weather)} days of weather.")
    
    # --- SYNTHESIS ENGINE ---
    print("🧪 Synthesizing 50,000 Delivery Samples...")
    
    samples = []
    
    # We generate 50k random samples
    for _ in range(50000):
        # Pick a random location
        hex_row = df_hex.sample(1).iloc[0]
        # Pick a random day
        weather_row = df_weather.sample(1).iloc[0]
        # Pick a random time (0 to 23 hours)
        hour_of_day = random.randint(7, 22) # Deliveries mostly happen 7 AM - 10 PM
        
        # --- THE PHYSICS FORMULA (Our "Ground Truth") ---
        
        # 1. Base Friction (Cooking + Pickup)
        base_delay = 10 
        
        # 2. Traffic Friction
        # Logic: High nodes + Peak Hours (8-10am, 5-8pm) = High Traffic
        is_peak = 1 if (8 <= hour_of_day <= 10) or (17 <= hour_of_day <= 20) else 0
        traffic_penalty = (hex_row['node_count'] * 0.05) * (1.5 if is_peak else 1.0)
        
        # 3. Weather Friction
        # Logic: Rain slows bikes drastically. Heat slows them slightly.
        rain_penalty = 0
        if weather_row['rainfall_mm'] > 5:
            rain_penalty = weather_row['rainfall_mm'] * 0.5 # 0.5 mins per mm of rain
        
        # 4. Flood Factor
        # Logic: If it rained heavily (>50mm) AND zone is flood prone -> DISASTER
        flood_penalty = 0
        if weather_row['rainfall_mm'] > 50 and hex_row['is_flood_prone'] == 1:
            flood_penalty = 45 # Massive delay (stuck in water)
            
        # Total Prediction
        total_delay = base_delay + traffic_penalty + rain_penalty + flood_penalty
        
        # Add some random noise (Real life is messy)
        total_delay += random.uniform(-2, 5)
        
        # Save sample
        samples.append({
            'hex_id': hex_row['hex_id'],
            'date': weather_row['log_date'],
            'hour': hour_of_day,
            'node_count': hex_row['node_count'],
            'road_length': hex_row['road_length_meters'],
            'is_flood_prone': hex_row['is_flood_prone'],
            'rainfall_mm': weather_row['rainfall_mm'],
            'is_peak': is_peak,
            'delay_minutes': round(max(5, total_delay), 1) # Cannot be less than 5 mins
        })
        
    # Convert to DataFrame
    df_train = pd.DataFrame(samples)
    
    # Save to CSV (This is what we will train the AI on)
    df_train.to_csv("training_data.csv", index=False)
    print("✅ Dataset generated: 'training_data.csv' (50,000 rows)")
    print(df_train.head())

if __name__ == "__main__":
    generate_synthetic_data()