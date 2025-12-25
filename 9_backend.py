from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import h3
import mysql.connector

# --- CONFIG ---
app = FastAPI(title="Chennai City Pulse API")

# Load the trained brain
print("🧠 Loading Model...")
model = joblib.load("chennai_delay_model.pkl")

DB_CONFIG = {
    'user': 'root',
    'password': 'rootpassword123',
    'host': '127.0.0.1',
    'port': 3307,
    'database': 'chennai_logistics'
}

# Define the "Shape" of the input data
class DeliveryRequest(BaseModel):
    latitude: float
    longitude: float
    rainfall_mm: float = 0.0 # Default to 0 if not provided
    is_peak_hour: int = 0    # 1 = Yes, 0 = No

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def get_hex_features(lat, lon):
    """
    Finds which hexagon this coordinate belongs to and gets its static data.
    """
    # 1. Convert Lat/Lon to H3 Address
    hex_id = h3.latlng_to_cell(lat, lon, 8)
    
    # 2. Query DB for this hex
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # Dictionary cursor gives us column names
    
    query = "SELECT node_count, road_length_meters, is_flood_prone FROM city_hexagons WHERE hex_id = %s"
    cursor.execute(query, (hex_id,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return result
    else:
        # If input is outside Chennai, return average values/defaults
        return {"node_count": 50, "road_length_meters": 5000, "is_flood_prone": 0}

@app.post("/predict_delay")
def predict_delay(req: DeliveryRequest):
    # 1. Get Location Context (from DB)
    features = get_hex_features(req.latitude, req.longitude)
    
    # 2. Prepare Input for Model
    # Must match the exact column order used in training!
    # ['hour', 'node_count', 'road_length', 'is_flood_prone', 'rainfall_mm', 'is_peak']
    
    # We use a dummy hour (e.g., 18:00) for now, or you could add it to input
    input_df = pd.DataFrame([{
        'hour': 18, 
        'node_count': features['node_count'],
        'road_length': features['road_length_meters'],
        'is_flood_prone': features['is_flood_prone'],
        'rainfall_mm': req.rainfall_mm,
        'is_peak': req.is_peak_hour
    }])
    
    # 3. Predict
    prediction = model.predict(input_df)[0]
    
    return {
        "status": "success",
        "location_context": features,
        "predicted_delay_minutes": round(float(prediction), 2)
    }

@app.get("/")
def health_check():
    return {"message": "Chennai City Pulse API is Online 🟢"}