#!/bin/sh
set -e

# Pick up explicit environment variable from Render or container environment
REQ_URL="${BACKEND_URL:-${VITE_BACKEND_URL:-${API_URL:-${BACKEND_SERVICE_URL:-${RENDER_BACKEND_URL:-}}}}}"

# Safely check if 'backend' hostname is resolvable in DNS (e.g. local Docker Compose network)
IS_LOCAL_COMPOSE=0
if nslookup backend >/dev/null 2>&1; then
    IS_LOCAL_COMPOSE=1
fi

if [ -n "$REQ_URL" ] && [ "$REQ_URL" != "http://backend:8000" ]; then
    TARGET_URL="$REQ_URL"
elif [ "$IS_LOCAL_COMPOSE" = "1" ]; then
    TARGET_URL="http://backend:8000"
else
    # Fallback for Render / Cloud Web Service when 'backend' host is unresolvable
    TARGET_URL="https://mplad-guardian-a1ah.onrender.com"
fi

# Strip trailing slashes
TARGET_URL="$(echo "$TARGET_URL" | sed 's#/*$##')"
export BACKEND_URL="$TARGET_URL"

echo "[40-backend-url.sh] Configuring Nginx proxy_pass to: ${BACKEND_URL}/api/"

# Substitute $BACKEND_URL into Nginx template
envsubst '$BACKEND_URL' < /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf
