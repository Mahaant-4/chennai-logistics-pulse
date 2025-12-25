import pandas as pd
import numpy as np
import mysql.connector
import joblib
from sklearn.metrics import mean_absolute_error, r2_score
import os

# Database Config
DB_CONFIG = {
    'user': 'root', 'password': 'rootpassword123',
    'host': '127.0.0.1', 'port': 3307, 'database': 'chennai_logistics'
}

def verify_model():
    print("🔌 Connecting to Database...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        # Fetch real city metrics (Road density, Flood risk)
        query = "SELECT node_count, road_length_meters, is_flood_prone FROM city_hexagons"
        df_hex = pd.read_sql(query, conn)
        conn.close()
        print(f"✅ Loaded {len(df_hex)} hexagons from Docker.")
    except Exception as e:
        print(f"❌ DB Error: {e}")
        return

    # --- 1. GENERATE SYNTHETIC TEST DATA ---
    print("🧪 Generating 5,000 synthetic scenarios to test logic...")
    
    # Randomly sample from our real hexagons
    test_data = df_hex.sample(5000, replace=True).reset_index(drop=True)
    
    # Add random weather/time conditions
    test_data['rainfall_mm'] = np.random.uniform(0, 150, 5000)
    test_data['hour'] = np.random.randint(0, 24, 5000)
    
    # Add logic for Peak Hour (8-10am, 5-8pm)
    test_data['is_peak'] = test_data['hour'].apply(lambda h: 1 if (8<=h<=10) or (17<=h<=20) else 0)
    
    # Rename columns to match model expectations
    test_data.rename(columns={'road_length_meters': 'road_length'}, inplace=True)

    # --- 2. CALCULATE "TRUE" DELAY (THE PHYSICS FORMULA) ---
    # This is the Logic we expect the model to have learned
    def calculate_physics_delay(row):
        base_delay = (row['road_length'] / 1000) * 2  # 2 mins per km base
        
        # Traffic Friction
        friction = 1.0
        if row['is_peak']: friction += 0.5            # +50% in peak
        if row['node_count'] > 15: friction += 0.3    # +30% in dense areas
        
        # Weather Friction
        if row['rainfall_mm'] > 5: friction += 0.2
        if row['rainfall_mm'] > 50: friction += 0.5   # Heavy rain
        if row['is_flood_prone'] and row['rainfall_mm'] > 30: 
            friction += 2.0                           # Flood Impact (Massive)

        return base_delay * friction

    # Apply the formula to get the "Correct Answer"
    y_truth = test_data.apply(calculate_physics_delay, axis=1)

    # --- 3. ASK THE MODEL ---
    print("🤖 Asking AI Model to predict...")
    model = joblib.load("chennai_delay_model.pkl")
    
    # Ensure columns are in correct order for the model
    X_test = test_data[['hour', 'node_count', 'road_length', 'is_flood_prone', 'rainfall_mm', 'is_peak']]
    
    y_pred = model.predict(X_test)

    # --- 4. SCORE CARD ---
    mae = mean_absolute_error(y_truth, y_pred)
    r2 = r2_score(y_truth, y_pred)

    print("\n" + "="*40)
    print(f"📉 Average Error:   {mae:.2f} minutes")
    print(f"📊 Accuracy Score:  {r2*100:.1f}%")
    print("="*40)
    
    if r2 > 0.85:
        print("✅ SUCCESS: The model understands the rules of traffic perfectly!")
    elif r2 > 0.60:
        print("⚠️ OKAY: The model gets the general idea but is a bit loose.")
    else:
        print("❌ FAIL: The model is guessing randomly. (Did you retrain it?)")

if __name__ == "__main__":
    verify_model()