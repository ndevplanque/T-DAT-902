FROM python:3.9-slim

# Installation des dépendances compatible avec ARM
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jdk \
    procps \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Définir JAVA_HOME - utiliser un chemin standard pour default-jdk
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH=$PATH:$JAVA_HOME/bin

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

# Créer un script d'entrée
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]