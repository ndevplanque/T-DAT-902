FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances système pour psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
RUN pip install --no-cache-dir pymongo psycopg2-binary

# Copier le script d'agrégation
COPY aggregation.py /app/aggregation.py

# Point d'entrée
CMD ["python", "/app/aggregation.py"]
