# 🚛 Chennai Logistics Pulse: Real-Time Digital Twin

![Python](https://img.shields.io/badge/Python-3.9-blue?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-ff4b4b?style=for-the-badge&logo=streamlit&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Container-2496ed?style=for-the-badge&logo=docker&logoColor=white)
![Status](https://img.shields.io/badge/Status-Live-success?style=for-the-badge)

**A Hyperlocal Logistics Intelligence Engine for Urban Transit Optimization.**

### 🔗 [View Live Demo on Hugging Face](https://huggingface.co/spaces/YOUR_USERNAME/Chennai-Logistics-Pulse)
*(Replace `YOUR_USERNAME` with your actual link)*

---

## 📖 Project Overview
**Chennai Logistics Pulse** is a data-driven dashboard designed to monitor and predict logistical friction points across Chennai's key industrial and IT corridors.

By integrating real-time traffic telemetry, hyperlocal weather conditions, and static infrastructure metrics, this application creates a "Digital Twin" of the city. It allows logistics managers to identify bottlenecks, predict delivery delays using Machine Learning, and visualize flood risks in real-time.

## ✨ Key Features
* **📍 Real-Time Traffic Integration:** Fetches live flow data from **50+ strategic probes** (North Port, Central Business District, OMR IT Corridor) using the **TomTom API**.
* **🌦️ Weather Impact Analysis:** Integrates live precipitation and temperature data via **Open-Meteo** to adjust delivery time estimates dynamically.
* **🤖 Predictive Analytics:** Uses a **Random Forest Regressor** to predict "Zone Transit Latency" based on road complexity, rain intensity, and time-of-day.
* **🌊 Flood Risk Detection:** Identifies and highlights zones prone to waterlogging (e.g., Velachery, Adyar) during high-rainfall events.
* **📦 Containerized Deployment:** Fully Dockerized application deployed on **Hugging Face Spaces** for consistent performance across environments.

---

## 🛠️ Tech Stack

| Component | Technology Used |
| :--- | :--- |
| **Frontend/Dashboard** | Streamlit |
| **Geospatial Viz** | PyDeck (3D Hexagon Layers) |
| **Database** | SQLite (Lightweight, Serverless) |
| **Machine Learning** | Scikit-Learn (Random Forest Regressor) |
| **APIs** | TomTom Traffic API, Open-Meteo Weather API |
| **Deployment** | Docker, Hugging Face Spaces |

---

## 📊 Data & Model Logic

### 1. Data Sources (Transparency)
This project blends real-world telemetry with synthetic infrastructure data to demonstrate a complete digital twin.

| Data Component | Source | Description |
| :--- | :--- | :--- |
| **Traffic Speeds** | 🔴 **Live (TomTom API)** | Real-time congestion factors relative to free-flow speeds from 50+ sensors. |
| **Weather** | 🔴 **Live (Open-Meteo)** | Live precipitation (mm) and temperature updates for 3 city zones. |
| **City Topology** | 🧪 **Simulated** | Hexagonal grid with attributes for road length and intersection density. |
| **Prediction Model** | 🧪 **Simulated** | Random Forest model trained on physics-based synthetic logistics scenarios. |

### 2. Machine Learning Logic
The **Random Forest Regressor** predicts the *Base Transit Time* (in minutes) for any given zone based on:
1.  **Road Length** (Meters)
2.  **Intersection Density** (Node Count)
3.  **Rainfall Intensity** (mm)
4.  **Flood Risk Flag** (0 or 1)
5.  **Peak Hour Status** (Is it 8-10 AM or 5-8 PM?)

$$\text{Final Delay} = (\text{ML Prediction} \times \text{Live Traffic Factor}) + \text{Rain Penalty}$$

---

## ⚙️ Installation & Setup

### Option 1: Run Locally (Python)

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/chennai-logistics-pulse.git](https://github.com/YOUR_USERNAME/chennai-logistics-pulse.git)
    cd chennai-logistics-pulse
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set Environment Variables (Optional)**
    * Create a `.env` file or export your API key. (The app runs in simulation mode if no key is provided).
    ```bash
    export TOMTOM_API_KEY="your_api_key_here"
    ```

4.  **Run the App**
    ```bash
    streamlit run 10_dashboard.py
    ```

### Option 2: Run with Docker

1.  **Build the Image**
    ```bash
    docker build -t chennai-logistics .
    ```

2.  **Run the Container**
    ```bash
    docker run -p 7860:7860 chennai-logistics
    ```
    *Access the app at `http://localhost:7860`*

---

## 📂 Project Structure

```text
chennai-logistics-pulse/
├── 10_dashboard.py         # Main Application Logic (Streamlit)
├── chennai_delay_model.pkl # Pre-trained ML Prediction Model
├── chennai.db              # SQLite Database (City Nodes & Attributes)
├── Dockerfile              # Container instructions
├── requirements.txt        # Python dependencies
└── README.md               # Documentation
