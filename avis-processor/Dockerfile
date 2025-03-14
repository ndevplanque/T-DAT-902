FROM bitnami/spark:3.4.1

USER root

# Installation des outils systèmes nécessaires
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-pip \
    python3-dev \
    netcat-traditional \
    wget \
    curl \
    dos2unix \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier uniquement les fichiers nécessaires
COPY requirements.txt word_processor.py ./
COPY submit.sh ./

# Installer les dépendances Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Télécharger le connecteur MongoDB Spark et placer dans le répertoire des jars
RUN mkdir -p /opt/bitnami/spark/jars && \
    wget -q https://repo1.maven.org/maven2/org/mongodb/spark/mongo-spark-connector_2.12/10.1.1/mongo-spark-connector_2.12-10.1.1.jar -O /opt/bitnami/spark/jars/mongo-spark-connector.jar && \
    wget -q https://repo1.maven.org/maven2/org/mongodb/mongodb-driver-sync/4.11.1/mongodb-driver-sync-4.11.1.jar -O /opt/bitnami/spark/jars/mongodb-driver-sync.jar && \
    wget -q https://repo1.maven.org/maven2/org/mongodb/mongodb-driver-core/4.11.1/mongodb-driver-core-4.11.1.jar -O /opt/bitnami/spark/jars/mongodb-driver-core.jar && \
    wget -q https://repo1.maven.org/maven2/org/mongodb/bson/4.11.1/bson-4.11.1.jar -O /opt/bitnami/spark/jars/bson.jar

# Télécharger également le connecteur pour spaCy
RUN pip3 install spacy && python3 -m spacy download fr_core_news_sm

# Corriger les fins de ligne et ajouter les permissions d'exécution
RUN dos2unix submit.sh && \
    chmod 755 submit.sh

# Script de démarrage
CMD ["/bin/bash", "/app/submit.sh"]