FROM python:3.11-slim

# Installation des dépendances système
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    default-jdk \
    wget \
    procps \  
    # Ajout de procps pour avoir la commande ps
    && rm -rf /var/lib/apt/lists/*

# Configuration de Java
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH=$PATH:$JAVA_HOME/bin

# Création du répertoire de travail
WORKDIR /app

# Copie des requirements et installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie des fichiers du projet
COPY . .

# Variables d'environnement
ENV POSTGRES_HOST=postgres
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=gis_db
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV PYSPARK_PYTHON=/usr/bin/python3
ENV PYSPARK_DRIVER_PYTHON=/usr/bin/python3
# Utiliser le chemin vers le JAR monté via volume
ENV SPARK_CLASSPATH=/opt/bitnami/spark/custom-jars
ENV JAVA_OPTS="-Dio.netty.tryReflectionSetAccessible=true --add-opens=java.base/java.nio=ALL-UNNAMED --add-opens=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED"

# Commande par défaut
CMD ["python", "csv_treatment.py"]