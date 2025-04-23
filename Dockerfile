# xm-sync/Dockerfile

# 1. Lightweight Python base
FROM python:3.11-slim

# 2. Set working dir
WORKDIR /app

# 3. Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy application code
COPY . .

# 5. Expose health‐check port
EXPOSE 8080

# 6. Start the hourly sync loop + HTTP server
CMD ["./entrypoint.sh"]
