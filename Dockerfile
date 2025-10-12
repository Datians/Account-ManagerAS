FROM python:3.11-slim
ENV FLASK_APP="app:create_app"
# libs para pandas/openpyxl/psycopg2 si luego usas Postgres
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala deps antes para cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el proyecto
COPY . .

# Fly asigna $PORT
ENV PORT=8000
# (opcional) asegurar temp en memoria para gunicorn
ENV PYTHONUNBUFFERED=1

# Arranque con gunicorn (usa el wsgi.py)
CMD ["bash","-lc","gunicorn wsgi:app --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:${PORT}"]
