FROM python:3.11-slim
RUN apt-get update && apt-get install -y netcat-openbsd && apt-get clean

# Installation des dépendances système
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    default-jdk \
    wget \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Configuration de Java
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH=$JAVA_HOME/bin:$PATH

# Définir le répertoire de travail
WORKDIR /app

# Copier les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier les fichiers du projet
COPY . .

# Variables d'environnement (peuvent être redéfinies dans docker-compose.yml)
ENV POSTGRES_HOST=postgres
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=gis_db
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV PYSPARK_PYTHON=/usr/local/bin/python
ENV PYSPARK_DRIVER_PYTHON=/usr/local/bin/python

# SPARK_CLASSPATH pour le driver PostgreSQL (monté via volume)
ENV SPARK_CLASSPATH=/app/jars/postgresql-42.7.4.jar

COPY wait-for-postgres.sh /wait-for-postgres.sh
RUN chmod +x /wait-for-postgres.sh
ENTRYPOINT ["/wait-for-postgres.sh"]

# Commande par défaut
CMD ["python", "csv_treatment.py"]
