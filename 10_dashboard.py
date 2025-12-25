import streamlit as st
import pandas as pd
import pydeck as pdk
import mysql.connector
import sqlite3
import joblib
import requests
from datetime import datetime
import pytz
import os
import time
import numpy as np

# --- 1. CONFIGURATION ---
st.set_page_config(
    layout="wide", 
    page_title="Chennai Logistics Pulse", 
    page_icon="📡", 
    initial_sidebar_state="expanded" 
)

# --- 2. CSS: FULL SCREEN MAP + NORMAL SIDEBAR ---
st.markdown("""
<style>
    /* 1. REMOVE PADDING FROM MAIN AREA (Map touches edges) */
    .block-container { 
        padding-top: 0rem !important; 
        padding-bottom: 0rem !important; 
        padding-left: 0rem !important; 
        padding-right: 0rem !important; 
        margin: 0px !important;
        max-width: 100% !important;
    }
    
    /* 2. TRANSPARENT HEADER */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        z-index: 1;
            
            
    }

    /* 3. FLOATING TITLE (Centered Top) */
    .floating-title {
        position: fixed;
        top: 30px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 1000;
        background-color: rgba(20, 20, 20, 0.9);
        padding: 8px 24px;
        border-radius: 24px;
        border: 1px solid #444;
        color: white;
        font-family: sans-serif;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .floating-title h1 { margin: 0; font-size: 1rem !important; color: white !important; font-weight: 700; display: inline-block;}
    .floating-title span { font-size: 0.8rem; color: #bbb; margin-left: 10px; border-left: 1px solid #555; padding-left: 10px;}

    /* 4. FLOATING TOGGLE (Top Right) */
    div[data-testid="stRadio"] {
        position: fixed;
        top: 70px;
        right: 20px;
        z-index: 1000;
        background-color: rgba(20, 20, 20, 0.9);
        padding: 8px 16px;
        border-radius: 8px;
        border: 1px solid rgba(0,0,0,0.1);
        color: white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    div[data-testid="stRadio"] label p { 
        font-size: 0.9rem !important; 
        color: white !important; 
        font-weight: bold !important; 
    }

    /* 5. SIDEBAR STYLING (Normal Docked) */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #ddd;
        
    }
    
    /* Progress Bar Styling */
    .stProgress > div > div > div > div {
        background-color: #00C853;
    }
    
    div.stButton > button:first-child {
        background-color: #00C853; 
        color: white !important; 
        border: none; 
        border-radius: 8px; 
        height: 45px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)



mode = st.radio("System Mode", ["🟢 Simulate", "🔴 LIVE"], horizontal=True, label_visibility="collapsed")


# --- 4. LOGIC & DATA ---
TOMTOM_API_KEY = "fNlCgkiJhPwMNn62aIS0QwsUKxv2AJ24" # 🔴 PASTE KEY
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", 3307))
DB_CONFIG = {'user': 'root', 'password': 'rootpassword123', 'host': DB_HOST, 'port': DB_PORT, 'database': 'chennai_logistics'}
IST = pytz.timezone('Asia/Kolkata')

TRAFFIC_PROBES = [
    # NORTH
    {"name": "⚓ Ennore", "lat": 13.2000, "lon": 80.3200}, {"name": "🏭 Manali", "lat": 13.1667, "lon": 80.2667},
    {"name": "🚛 Red Hills", "lat": 13.1500, "lon": 80.1900}, {"name": "🏭 Tiruvottiyur", "lat": 13.1600, "lon": 80.3000},
    {"name": "🏘️ Tondiarpet", "lat": 13.1200, "lon": 80.2800}, {"name": "🚢 Royapuram", "lat": 13.1100, "lon": 80.2900},
    {"name": "🚉 Perambur", "lat": 13.1143, "lon": 80.2405}, {"name": "🛣️ Madhavaram", "lat": 13.1400, "lon": 80.2300},
    {"name": "🛣️ Vyasarpadi", "lat": 13.1100, "lon": 80.2600},
    # WEST
    {"name": "🏭 Ambattur", "lat": 13.0900, "lon": 80.1600}, {"name": "🏘️ Avadi", "lat": 13.1000, "lon": 80.1000},
    {"name": "🏘️ Mogappair", "lat": 13.0800, "lon": 80.1700}, {"name": "🛣️ Poonamallee", "lat": 13.0500, "lon": 80.0900},
    {"name": "🏗️ Maduravoyal", "lat": 13.0600, "lon": 80.1600}, {"name": "🏗️ Porur", "lat": 13.0382, "lon": 80.1565},
    {"name": "🛣️ Vanagaram", "lat": 13.0600, "lon": 80.1400}, {"name": "🛣️ Thirumazhisai", "lat": 13.0500, "lon": 80.0600},
    {"name": "🏘️ Valasaravakkam", "lat": 13.0400, "lon": 80.1700},
    # CENTRAL
    {"name": "🏢 Anna Salai", "lat": 13.0550, "lon": 80.2550}, {"name": "🛍️ T. Nagar", "lat": 13.0400, "lon": 80.2350},
    {"name": "🏛️ Central", "lat": 13.0827, "lon": 80.2707}, {"name": "🏥 Egmore", "lat": 13.0732, "lon": 80.2609},
    {"name": "🛣️ Koyambedu", "lat": 13.0694, "lon": 80.2052}, {"name": "🎬 Vadapalani", "lat": 13.0500, "lon": 80.2121},
    {"name": "🌴 Nungambakkam", "lat": 13.0626, "lon": 80.2285}, {"name": "🕉️ Mylapore", "lat": 13.0368, "lon": 80.2676},
    {"name": "🏥 Kilpauk", "lat": 13.0800, "lon": 80.2400}, {"name": "🏖️ Marina", "lat": 13.0500, "lon": 80.2800},
    {"name": "🏘️ Triplicane", "lat": 13.0550, "lon": 80.2700}, {"name": "🏘️ Alwarpet", "lat": 13.0300, "lon": 80.2500},
    # SOUTH
    {"name": "✈️ Airport", "lat": 12.9800, "lon": 80.1650}, {"name": "🛣️ Guindy", "lat": 13.0067, "lon": 80.2206},
    {"name": "🌊 Adyar", "lat": 13.0012, "lon": 80.2565}, {"name": "🏠 Velachery", "lat": 12.9750, "lon": 80.2207},
    {"name": "🚉 Tambaram", "lat": 12.9229, "lon": 80.1275}, {"name": "🛣️ Chromepet", "lat": 12.9500, "lon": 80.1400},
    {"name": "🛣️ Pallavaram", "lat": 12.9600, "lon": 80.1500}, {"name": "🦁 Vandalur", "lat": 12.8900, "lon": 80.0800},
    {"name": "🏭 Oragadam", "lat": 12.8300, "lon": 80.0000}, {"name": "🛣️ Perungalathur", "lat": 12.9000, "lon": 80.0900},
    {"name": "🏘️ Medavakkam", "lat": 12.9100, "lon": 80.1900},
    # OMR
    {"name": "🏖️ Thiruvanmiyur", "lat": 12.9830, "lon": 80.2594}, {"name": "🛣️ OMR", "lat": 12.9900, "lon": 80.2500},
    {"name": "🛣️ Perungudi", "lat": 12.9600, "lon": 80.2400}, {"name": "💻 Thoraipakkam", "lat": 12.9400, "lon": 80.2300},
    {"name": "💻 Sholinganallur", "lat": 12.9010, "lon": 80.2279}, {"name": "🏘️ Navalur", "lat": 12.8600, "lon": 80.2200},
    {"name": "🏢 Siruseri", "lat": 12.8300, "lon": 80.2200}, {"name": "🏖️ Kovalam", "lat": 12.7900, "lon": 80.2500},
    {"name": "🛣️ Kelambakkam", "lat": 12.7800, "lon": 80.2200},
]

if 'traffic_data' not in st.session_state:
    st.session_state['traffic_data'] = {'factor': 1.0, 'breakdown': [], 'rain': 0.0, 'temp': 0.0, 'last_updated': None}

@st.cache_resource
def load_model(): return joblib.load("chennai_delay_model.pkl")
model = load_model()

def get_db_data():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        query = "SELECT hex_id, latitude, longitude, place_name, node_count, road_length_meters, is_flood_prone FROM city_hexagons"
        df = pd.read_sql(query, conn)
        conn.close()
        
        def calculate_flood_risk(row):
            lat, lon = row['latitude'], row['longitude']
            if 12.96 < lat < 12.99 and 80.21 < lon < 80.23: return 1 
            if 13.00 < lat < 13.02 and 80.24 < lon < 80.27: return 1 
            if lat > 13.16: return 1 
            if 12.88 < lat < 12.92 and 80.22 < lon < 80.24: return 1
            return 0

        df['is_flood_prone'] = df.apply(calculate_flood_risk, axis=1)
        return df
    except: return pd.DataFrame()

def fetch_live_data():
    # 1. SETUP PROGRESS BAR
    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    
    rain = 0.0; temp = 30.0
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=13.08&longitude=80.27&current=temperature_2m,precipitation,rain,showers"
        resp = requests.get(url, timeout=3).json()
        rain = float(resp['current'].get('precipitation', 0) + resp['current'].get('rain', 0))
        temp = float(resp['current'].get('temperature_2m', 0))
    except: pass

    results = []
    session = requests.Session()
    total = len(TRAFFIC_PROBES)
    
    if "xx" in TOMTOM_API_KEY:
         import random
         for i, site in enumerate(TRAFFIC_PROBES):
             # Update Progress
             progress_bar.progress((i + 1) / total)
             status_text.caption(f"📡 Scanning: {site['name']}...")
             time.sleep(0.02) # Artificial delay to see the bar
             
             results.append({"name": site['name'], "lat": site['lat'], "lon": site['lon'], "raw_factor": random.uniform(1.0, 1.8), "Load": f"x{random.uniform(1.0, 1.8):.2f}", "St": "🟢"})
    else:
        for i, site in enumerate(TRAFFIC_PROBES):
            progress_bar.progress((i + 1) / total)
            status_text.caption(f"📡 Pinging: {site['name']}...")
            
            try:
                url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point={site['lat']},{site['lon']}&key={TOMTOM_API_KEY}"
                resp = session.get(url, timeout=2)
                if resp.status_code == 200:
                    data = resp.json().get('flowSegmentData', {})
                    curr = data.get('currentSpeed', 30); free = data.get('freeFlowSpeed', 30)
                    factor = max(1.0, min(free / max(curr, 1), 3.5))
                    icon = "🟢" if factor < 1.15 else ("🔴" if factor > 1.3 else "🟠")
                    results.append({"name": site['name'], "lat": site['lat'], "lon": site['lon'], "raw_factor": factor, "Load": f"x{factor:.2f}", "St": icon})
                else: results.append({"name": site['name'], "lat": site['lat'], "lon": site['lon'], "raw_factor": 1.0, "Load": "ERR", "St": "⚠️"})
            except: results.append({"name": site['name'], "lat": site['lat'], "lon": site['lon'], "raw_factor": 1.0, "Load": "OFF", "St": "🔌"})

    # CLEANUP PROGRESS BAR
    progress_bar.empty()
    status_text.empty()

    avg_factor = sum([r['raw_factor'] for r in results]) / len(results) if results else 1.0
    st.session_state['traffic_data'] = {
        'factor': avg_factor, 
        'breakdown': results, 
        'rain': rain, 
        'temp': temp, 
        'last_updated': datetime.now(IST).strftime("%H:%M:%S")
    }

# --- 5. SIDEBAR CONTENT ---
with st.sidebar:
    st.markdown("### 🎛️ Control Panel")
    
    if mode == "🔴 LIVE":
        if st.button("🔄 REFRESH DATA"): 
            fetch_live_data()
            st.rerun() 
        
        data = st.session_state['traffic_data']
        if data['last_updated']:
            st.success(f"Online: {data['last_updated']}")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("🌧️ Rain", f"{data['rain']}mm")
            c2.metric("🌡️ Temp", f"{data.get('temp', 0)}°C")
            c3.metric("🚦 Load", f"x{data['factor']:.2f}")
            
            rain_input = data['rain']; traffic_factor = data['factor']
            time_input = datetime.now(IST).hour
        else:
            st.error("System Offline")
            rain_input = 0; traffic_factor = 1.0; time_input = 12
    else:
        st.info("🧪 Simulation Mode")
        rain_input = st.slider("🌧️ Rainfall (mm)", 0, 150, 0)
        time_input = st.slider("⏰ Time of Day", 0, 23, 18)
        traffic_factor = st.slider("🚗 Traffic Multiplier", 0.5, 3.0, 1.0)
    
    is_peak = 1 if (8 <= time_input <= 10) or (17 <= time_input <= 20) else 0
    
    st.markdown("---")
    
    # ANALYSIS
    df_hex = get_db_data()
    
    if not df_hex.empty:
        input_data = pd.DataFrame({
            'hour': [time_input] * len(df_hex),
            'node_count': df_hex['node_count'] / 10,
            'road_length': df_hex['road_length_meters'] / 10,
            'is_flood_prone': df_hex['is_flood_prone'],
            'rainfall_mm': [rain_input] * len(df_hex),
            'is_peak': [is_peak] * len(df_hex)
        })
        raw_pred = model.predict(input_data)
        base_transit_time = np.clip(raw_pred, 3, 20)
        
        if mode == "🔴 LIVE" and st.session_state['traffic_data']['breakdown']:
            sensor_data = st.session_state['traffic_data']['breakdown']
            sensor_locs = np.array([[s['lat'], s['lon']] for s in sensor_data])
            sensor_factors = np.array([s['raw_factor'] for s in sensor_data])
            hex_locs = df_hex[['latitude', 'longitude']].values
            dists_squared = ((hex_locs[:, None, :] - sensor_locs[None, :, :]) ** 2).sum(axis=2)
            nearest_idx = dists_squared.argmin(axis=1)
            min_dists_sq = dists_squared.min(axis=1)
            final_factors = np.where(min_dists_sq > 0.0008, 1.0, sensor_factors[nearest_idx])
            df_hex['traffic_factor'] = final_factors
            df_hex['predicted_delay'] = np.clip((base_transit_time * final_factors) + (rain_input * 0.2), 2, 60).round(0)
        else:
            df_hex['traffic_factor'] = traffic_factor
            df_hex['predicted_delay'] = np.clip((base_transit_time * traffic_factor) + (rain_input * 0.2), 2, 60).round(0)
        df_hex['traffic_display'] = df_hex['traffic_factor'].apply(lambda x: f"x{x:.2f}")

        st.markdown("### 📊 Network Health")
        avg_delay = df_hex['predicted_delay'].mean()
        max_delay = df_hex['predicted_delay'].max()
        est_speed = 30 / (traffic_factor if mode != "🔴 LIVE" else st.session_state['traffic_data']['factor']) 
        active_hotspots = len(df_hex[df_hex['traffic_factor'] > 1.25])
        
        status_color = "green" if avg_delay < 15 else ("orange" if avg_delay < 30 else "red")
        status_text = "Smooth Flow" if avg_delay < 15 else ("Moderate Congestion" if avg_delay < 30 else "Gridlock Alert")
        st.markdown(f"**Status:** :{status_color}[{status_text}]")

        r1c1, r1c2 = st.columns(2)
        r1c1.metric("Avg Delay", f"{avg_delay:.0f} min")
        r1c2.metric("Max Delay", f"{max_delay:.0f} min")
        
        r2c1, r2c2 = st.columns(2)
        r2c1.metric("Est. Speed", f"{est_speed:.0f} km/h")
        r2c2.metric("Hotspots", f"{active_hotspots}")
        
        if rain_input > 50:
            st.error(f"🌊 FLOOD WARNING ACTIVE")
            flood_zones = len(df_hex[df_hex['is_flood_prone'] == 1])
            st.caption(f"{flood_zones} Zones at High Risk (Velachery, Adyar)")

# --- 6. MAP VISUALIZATION ---
def get_realistic_color(row):
    delay = row['predicted_delay']; factor = row['traffic_factor']; rain = rain_input; flood = row['is_flood_prone']
    if flood == 1 and rain > 50: return [0, 119, 255, 200]
    if factor > 1.3 or delay > 30: return [255, 0, 0, 200]
    elif factor > 1.15 or delay > 15: return [255, 140, 0, 160]
    else: return [0, 255, 100, 100]

if not df_hex.empty:
    df_hex['color'] = df_hex.apply(get_realistic_color, axis=1)

layer = pdk.Layer(
    "H3HexagonLayer",
    df_hex,
    pickable=True,
    extruded=False, 
    stroked=True,            
    filled=True,
    get_hexagon="hex_id",
    get_fill_color="color",
    get_line_color=[255, 255, 255, 80],
    line_width_min_pixels=2,
    opacity=0.1 
)

view_state = pdk.ViewState(latitude=13.04, longitude=80.20, zoom=10.5, pitch=0)

tooltip = {
    "html": """
    <div style="background-color: #111; color: #fff; padding: 10px; border-radius: 4px;">
        <b>📍 {place_name}</b><br/>
        Transit time: <span style="color: #ffeb3b;">{predicted_delay} min</span><br/>
        Traffic Load: <span style="color: #00e676;">{traffic_display}</span>
    </div>
    """,
    "style": {"border": "none"}
}

st.pydeck_chart(pdk.Deck(
    map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    initial_view_state=view_state,
    layers=[layer],
    tooltip=tooltip
), use_container_width=True, height=1000)