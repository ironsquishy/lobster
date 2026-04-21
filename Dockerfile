FROM python:3.12-slim

# Prevent Python from buffering stdout/stderr so logs appear immediately
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install useful debugging/runtime tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    jq \
    iputils-ping \
    netcat-openbsd \
    dnsutils \
    sqlite3 \
    procps \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY app ./app
COPY data ./data

# Expose Lobster API port
EXPOSE 4000

# Health check
HEALTHCHECK --interval=60s --timeout=5s --retries=5 CMD curl -fsS http://127.0.0.1:4000/healthz || exit 1

# Start app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4000"]