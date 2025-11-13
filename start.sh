#!/bin/sh
echo "🚀 Starting Gunicorn on port ${PORT:-5000}"
exec gunicorn run:app --bind 0.0.0.0:${PORT:-5000}
