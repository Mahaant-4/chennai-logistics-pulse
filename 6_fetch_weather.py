import mysql.connector
import requests
import pandas as pd
from datetime import date, timedelta

# --- CONFIG ---
DB_CONFIG = {
    'user': 'root',
    'password': 'rootpassword123',
    'host': '127.0.0.1',
    'port': 3307,
    'database': 'chennai_logistics'
}

# Coordinates for Chennai Center
LAT = 13.0827
LON = 80.2707

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def fetch_historical_weather():
    print("🌤 Preparing to fetch Weather History...")
    
    # Define Date Range: Jan 1, 2024 to Yesterday
    start_date = "2024-01-01"
    end_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Open-Meteo API URL
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ["temperature_2m_max", "precipitation_sum"],
        "timezone": "Asia/Kolkata"
    }
    
    try:
        print(f"🌍 Calling Open-Meteo API ({start_date} to {end_date})...")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status() # Raises error if status is 404/500
        
        data = response.json()
        
        # Parse the JSON response
        daily_data = data['daily']
        dates = daily_data['time']
        temps = daily_data['temperature_2m_max']
        rains = daily_data['precipitation_sum']
        
        weather_records = []
        for d, t, r in zip(dates, temps, rains):
            # Handle None values (sometimes sensors fail)
            t = t if t is not None else 30.0
            r = r if r is not None else 0.0
            weather_records.append((d, r, t))
            
        print(f"   Received {len(weather_records)} days of weather data.")
        
        # Insert into Database
        save_to_db(weather_records)

    except requests.exceptions.RequestException as e:
        print(f"❌ API Connection Failed: {e}")

def save_to_db(records):
    print("💾 Saving to MySQL...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # INSERT IGNORE allows us to re-run the script without crashing on duplicates
    query = """
        INSERT IGNORE INTO weather_history (log_date, rainfall_mm, max_temp_c)
        VALUES (%s, %s, %s)
    """
    
    cursor.executemany(query, records)
    conn.commit()
    print("✅ Weather History Updated Successfully!")
    
    conn.close()

if __name__ == "__main__":
    fetch_historical_weather()