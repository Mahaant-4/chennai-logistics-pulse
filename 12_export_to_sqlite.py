import mysql.connector
import sqlite3
import pandas as pd
import os

print("📂 Starting Backup...")

# 1. Connect to Docker MySQL
try:
    mysql_conn = mysql.connector.connect(
        user='root', password='rootpassword123',
        host='127.0.0.1', port=3307, database='chennai_logistics'
    )
    print("✅ Connected to MySQL.")
except Exception as e:
    print(f"❌ MySQL Error: {e}")
    exit()

# 2. Connect to SQLite
sqlite_file = "chennai.db"
sqlite_conn = sqlite3.connect(sqlite_file)

# 3. Copy Data
query = "SELECT hex_id, place_name, node_count, road_length_meters, is_flood_prone FROM city_hexagons"
df = pd.read_sql(query, mysql_conn)
df.to_sql("city_hexagons", sqlite_conn, if_exists="replace", index=False)

print(f"✅ Success! Saved {len(df)} rows to {sqlite_file}")
mysql_conn.close()
sqlite_conn.close()