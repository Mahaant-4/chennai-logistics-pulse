import mysql.connector
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb
import joblib

# Database Config
DB_CONFIG = {
    'user': 'root', 'password': 'rootpassword123',
    'host': '127.0.0.1', 'port': 3307, 'database': 'chennai_logistics'
}

def train_new_model():
    print("🔌 Connecting to Docker DB...")
    conn = mysql.connector.connect(**DB_CONFIG)
    
    # 1. Fetch Real Hexagons
    query = "SELECT hex_id, node_count, road_length_meters, is_flood_prone FROM city_hexagons"
    df_hex = pd.read_sql(query, conn)
    conn.close()
    print(f"✅ Loaded {len(df_hex)} hexagons.")

    # 2. Generate Training Data (10,000 Samples)
    print("🧪 Generating Training Data...")
    df_train = df_hex.sample(10000, replace=True).reset_index(drop=True)
    
    # Random Inputs
    df_train['rainfall_mm'] = np.random.uniform(0, 150, 10000)
    df_train['hour'] = np.random.randint(0, 24, 10000)
    df_train['is_peak'] = df_train['hour'].apply(lambda h: 1 if (8<=h<=10) or (17<=h<=20) else 0)
    
    # Rename for consistency
    df_train.rename(columns={'road_length_meters': 'road_length'}, inplace=True)

    # --- THE GOLDEN LOGIC (Target Variable) ---
    def calculate_delay(row):
        # Base: 2 mins per km
        delay = (row['road_length'] / 1000) * 2.0
        
        # Traffic Multipliers
        traffic_factor = 1.0
        if row['is_peak']: traffic_factor += 0.4          # 40% slower in peak
        if row['node_count'] > 20: traffic_factor += 0.2  # 20% slower in dense areas
        
        # Weather Multipliers
        weather_factor = 1.0
        if row['rainfall_mm'] > 10: weather_factor += 0.2
        if row['rainfall_mm'] > 50: weather_factor += 0.5
        if row['is_flood_prone'] and row['rainfall_mm'] > 30:
            weather_factor += 2.0                         # Flood disaster!

        final_delay = delay * traffic_factor * weather_factor
        
        # Add a little randomness (Noise) so it's not perfect
        noise = np.random.normal(0, 2) 
        return max(0, final_delay + noise)

    df_train['delay_minutes'] = df_train.apply(calculate_delay, axis=1)

    # 3. Train Model
    print("🧠 Training XGBoost Model...")
    features = ['hour', 'node_count', 'road_length', 'is_flood_prone', 'rainfall_mm', 'is_peak']
    X = df_train[features]
    y = df_train['delay_minutes']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    
    model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=200, learning_rate=0.05)
    model.fit(X_train, y_train)
    
    # 4. Evaluate
    preds = model.predict(X_test)
    r2 = r2_score(y_test, preds)
    mae = mean_absolute_error(y_test, preds)
    
    print(f"📊 New Accuracy (R2): {r2*100:.2f}%")
    print(f"📉 Avg Error (MAE):   {mae:.2f} min")
    
    # 5. Save
    joblib.dump(model, "chennai_delay_model.pkl")
    print("💾 Saved new model to 'chennai_delay_model.pkl'")

if __name__ == "__main__":
    train_new_model()