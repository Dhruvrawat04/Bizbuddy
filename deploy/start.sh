#!/bin/bash
set -e

PORT="${PORT:-10000}"

# Make nginx listen on the host-provided PORT
sed -i "s/listen 10000;/listen ${PORT};/" /etc/nginx/nginx.conf

echo "==> Starting Mart1 FastAPI on :8000"
cd /app/mart1
uvicorn api_server:app --host 127.0.0.1 --port 8000 --workers 1 &
MART1_PID=$!

echo "==> Starting Supermarket Flask on :5001 (mounted at /supermarket)"
cd /app/supermarket
export FLASK_ENV="${FLASK_ENV:-production}"
gunicorn wsgi_subdir:application \
  --bind 127.0.0.1:5001 \
  --workers 1 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - &
SM_PID=$!

sleep 2

echo "==> Starting nginx on :${PORT}"
nginx -g "daemon off;" &
NGINX_PID=$!

echo "==> BizBuddy is up"
echo "    App home:     http://0.0.0.0:${PORT}/"
echo "    Mart1 API:    http://0.0.0.0:${PORT}/api/"
echo "    Supermarket:  http://0.0.0.0:${PORT}/supermarket/"

wait -n $MART1_PID $SM_PID $NGINX_PID
EXIT_CODE=$?
echo "==> A process exited (code $EXIT_CODE) — shutting down"
kill $MART1_PID $SM_PID $NGINX_PID 2>/dev/null || true
exit $EXIT_CODE
