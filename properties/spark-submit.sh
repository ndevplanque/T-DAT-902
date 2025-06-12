#!/bin/bash

echo "Lancement du traitement Spark..."
spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --jars /opt/bitnami/spark/custom-jars/postgresql-42.7.4.jar \
  /app/csv_treatment.py
