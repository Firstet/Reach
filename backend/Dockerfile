FROM python:3.12-slim

WORKDIR /app

# System dependencies for Playwright + psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (conditionally, only when LINKEDIN_ENABLED)
RUN python -m playwright install chromium --with-deps || true

COPY . .

EXPOSE 8000
