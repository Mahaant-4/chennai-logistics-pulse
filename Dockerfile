# 1. Use Python 3.9 Slim (Lightweight Linux)
FROM python:3.9-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Install System Dependencies (Required for some Python libraries)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your code into the container
COPY . .

# 6. Open the Streamlit port
EXPOSE 8501

# 7. Run the App
# --server.address=0.0.0.0 is crucial for Docker networking
CMD ["streamlit", "run", "10_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]