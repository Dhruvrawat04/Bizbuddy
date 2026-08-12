# ============================================================
# BizBuddy — single-container deploy (Mart1 + Supermarket)
# One URL:
#   /              → Mart1 React frontend
#   /api/*         → Mart1 FastAPI backend
#   /supermarket/* → Supermarket Flask analytics
# ============================================================

# ---------- Stage 1: build React frontend ----------
FROM node:20-alpine AS frontend-build
WORKDIR /frontend
COPY mart1/frontend/package.json mart1/frontend/package-lock.json* ./
RUN npm install
COPY mart1/frontend/ ./
# Same-origin API — no hardcoded external URL needed
ENV VITE_API_URL=/api
RUN npm run build

# ---------- Stage 2: runtime ----------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

WORKDIR /app

# System deps (nginx + build tools for some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
        nginx \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python deps — both apps
COPY mart1/requirements.txt /tmp/mart1-req.txt
COPY supermarket/requirements.txt /tmp/sm-req.txt
RUN pip install --no-cache-dir -r /tmp/mart1-req.txt -r /tmp/sm-req.txt \
    && pip install --no-cache-dir gunicorn

# App code
COPY mart1/ /app/mart1/
COPY supermarket/ /app/supermarket/

# Built frontend → nginx html root
COPY --from=frontend-build /frontend/dist /usr/share/nginx/html

# Nginx + process starter
COPY deploy/nginx.conf /etc/nginx/nginx.conf
COPY deploy/start.sh /app/start.sh
RUN chmod +x /app/start.sh \
    && mkdir -p /app/supermarket/uploads /var/log/nginx /var/lib/nginx /run

EXPOSE 10000

# Single public port (Render sets $PORT; start.sh respects it)
CMD ["/app/start.sh"]
