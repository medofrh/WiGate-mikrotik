# syntax=docker/dockerfile:1

# ---------- 1. Vue-Oberflaeche bauen ----------
FROM node:22-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---------- 2. Python-Basis ----------
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app

# ---------- 3. Tests (docker build --target test .) ----------
FROM base AS test
COPY backend/requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY backend/tests ./tests
RUN pytest -q

# ---------- 4. Laufzeit ----------
FROM base AS runtime
COPY --from=frontend /build/dist ./static
RUN useradd --system --uid 10001 wigate && chown -R wigate:wigate /app
USER wigate
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
