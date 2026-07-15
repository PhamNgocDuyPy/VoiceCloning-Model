# Stage 1: Build React Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/web_app/frontend
COPY web_app/frontend/package*.json ./
RUN npm install
COPY web_app/frontend/ ./
RUN npm run build

# Stage 2: Build Python Backend
FROM python:3.10-slim
WORKDIR /app

# Install system dependencies (ffmpeg is needed for video dubbing)
RUN apt-get update && apt-get install -y ffmpeg libsndfile1 && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY web_app/backend/requirements.txt /app/web_app/backend/
RUN pip install --no-cache-dir -r /app/web_app/backend/requirements.txt

# Copy backend code and models
COPY web_app/backend /app/web_app/backend
COPY web_app/static /app/web_app/static
COPY model /app/model

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/web_app/frontend/dist /app/web_app/frontend/dist

# Ensure outputs directory exists
RUN mkdir -p /app/web_app/static/outputs

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app

# Start the application
CMD ["uvicorn", "web_app.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
