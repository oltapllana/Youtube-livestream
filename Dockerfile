# ── Stage 1: Build Vue.js frontend ───────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --ignore-scripts 2>/dev/null || npm install
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python runtime ─────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Copy built frontend from stage 1
COPY --from=frontend-build /frontend/dist ./frontend/dist

# Create required directories
RUN mkdir -p logs app/algorithm/AA_25-26/data/input app/algorithm/AA_25-26/data/output

# Environment
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production
ENV PORT=8000

EXPOSE 8000

# Start the server — Railway sets PORT env var automatically
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
