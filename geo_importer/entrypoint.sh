#!/bin/bash

# Afficher la version de Java
echo "Version de Java :"
java -version

# Configurer les options Java plus simples
export JAVA_OPTS="-Dio.netty.tryReflectionSetAccessible=true"
export PYSPARK_SUBMIT_ARGS="--conf spark.driver.extraJavaOptions=\"${JAVA_OPTS}\" pyspark-shell"

# Attendre que PostgreSQL soit prêt
echo "Attente du démarrage de PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "PostgreSQL est prêt !"

# Attendre que le namenode soit prêt
echo "Attente du démarrage du namenode..."
while ! nc -z namenode 9000; do
  sleep 1
done
echo "Namenode est prêt !"

# Attendre que Spark soit prêt
echo "Attente du démarrage de Spark..."
while ! nc -z spark-master 7077; do
  sleep 1
done
echo "Spark est prêt !"

sleep 10

# Exécuter le script d'importation
echo "Démarrage de l'importation des données géographiques..."
python /app/geojson_processing.py

echo "Importation terminée."