#!/bin/bash
set -e

# Variables d'environnement
SPARK_MASTER=${SPARK_MASTER:-"spark://spark-master:7077"}
MONGO_URI=${MONGO_URI:-"mongodb://root:rootpassword@mongodb:27017/"}
MONGO_DB=${MONGO_DB:-"villes_france"}
WAIT_FOR_SCRAPER=${WAIT_FOR_SCRAPER:-"true"}

echo "Starting Avis Processor Submitter..."
echo "Using Spark Master: $SPARK_MASTER"

# ----- Fonction wait-for intégrée -----

# Attendre qu'un hôte et un port soient disponibles
wait_for_connection() {
    local host=$1
    local port=$2
    local timeout=${3:-120}

    echo "Waiting up to $timeout seconds for $host:$port..."

    start_ts=$(date +%s)

    # Boucle d'attente
    while true; do
        (echo > /dev/tcp/$host/$port) >/dev/null 2>&1
        result=$?

        if [ $result -eq 0 ]; then
            end_ts=$(date +%s)
            echo "$host:$port is available after $((end_ts - start_ts)) seconds"
            break
        fi

        # Vérifier le timeout
        current_ts=$(date +%s)
        if [ $((current_ts - start_ts)) -gt $timeout ]; then
            echo "Timeout reached waiting for $host:$port after $timeout seconds"
            exit 1
        fi

        echo "Waiting for $host:$port... retrying in 1 second"
        sleep 1
    done
}

# ----- Fin de la fonction wait-for intégrée -----

# Attendre que MongoDB soit prêt
echo "Waiting for MongoDB to be ready..."
wait_for_connection mongodb 27017 120

# Si configuré pour attendre le scraper, on vérifie qu'il a ajouté des données
if [ "$WAIT_FOR_SCRAPER" = "true" ]; then
    echo "Waiting for scraper to add data..."
    # Attendre que le scraper ait ajouté des données (vérifier toutes les 30 secondes)
    while true; do
        # Utiliser mongosh pour vérifier le nombre de documents
        COUNT=$(mongosh --quiet $MONGO_URI $MONGO_DB --eval "db.villes.countDocuments({})")

        if [ "$COUNT" -gt 0 ]; then
            echo "Scraper has added $COUNT cities. Proceeding with processing."
            break
        else
            echo "Waiting for scraper to add data... No cities found yet."
            sleep 30
        fi
    done
fi

# Attendre que le Master Spark soit prêt
echo "Waiting for Spark Master to be ready..."
wait_for_connection spark-master 7077 120

echo "Submitting Spark job to process avis..."

# Soumettre le job Spark
spark-submit \
  --master $SPARK_MASTER \
  --deploy-mode client \
  --conf "spark.mongodb.input.uri=$MONGO_URI$MONGO_DB" \
  --conf "spark.mongodb.output.uri=$MONGO_URI$MONGO_DB" \
  --conf "spark.driver.extraJavaOptions=-Dlog4j.configuration=file:///opt/bitnami/spark/conf/log4j.properties" \
  --conf "spark.executor.extraJavaOptions=-Dlog4j.configuration=file:///opt/bitnami/spark/conf/log4j.properties" \
  --jars /opt/bitnami/spark/jars/mongo-spark-connector.jar,/opt/bitnami/spark/jars/mongodb-driver-sync.jar,/opt/bitnami/spark/jars/mongodb-driver-core.jar,/opt/bitnami/spark/jars/bson.jar \
  /app/word_processor.py $MONGO_URI $MONGO_DB

echo "Job submitted successfully!"