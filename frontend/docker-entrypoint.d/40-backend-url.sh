#!/bin/sh
set -e

# Default BACKEND_URL if not provided
: "${BACKEND_URL:=http://backend:8000}"

# Strip trailing slash if present
BACKEND_URL="$(echo "$BACKEND_URL" | sed 's#/*$##')"
export BACKEND_URL

# Perform envsubst ONLY for $BACKEND_URL so Nginx variables ($uri, $host, etc.) are untouched
envsubst '$BACKEND_URL' < /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf
