# Stage 1: Build React Frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /app/web_app/frontend
COPY web_app/frontend/package*.json ./
RUN npm install
COPY web_app/frontend/ ./
RUN npm run build

# Stage 2: Build Python Backend
FROM python:3.10-slim
WORKDIR /app

# Install system dependencies (ffmpeg is needed for video dubbing, git for viterbox)
RUN apt-get update && apt-get install -y ffmpeg libsndfile1 git && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY web_app/requirements.txt /app/web_app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /app/web_app/requirements.txt
RUN pip install --no-cache-dir --no-deps vieneu "viterbox @ git+https://github.com/iamdinhthuan/viterbox-tts.git"

# Copy backend code and models
COPY web_app/backend /app/web_app/backend
COPY model /app/model

# Ensure static directories exist (since Git ignores empty folders)
RUN mkdir -p /app/web_app/static/outputs
RUN mkdir -p /app/web_app/static/memes
RUN mkdir -p /app/web_app/static/presets

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
