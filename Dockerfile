# Use Python 3.10 slim image as base
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for frontend
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Copy backend
COPY backend /app/backend
WORKDIR /app/backend

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend
WORKDIR /app
COPY frontend /app/frontend
WORKDIR /app/frontend

# Install Node dependencies and build frontend
RUN npm install && npm run build

# Setup Flask environment
WORKDIR /app
ENV FLASK_APP=backend/app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 5000 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run backend and serve frontend
CMD ["sh", "-c", "cd /app && python -m gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app"]
