#!/bin/bash

# Afficher la version de Java
echo "Version de Java :"
java -version

# Afficher la version de Python
echo "Python version in driver container:"
python --version

# Configurer les options Java
export JAVA_OPTS="-Dio.netty.tryReflectionSetAccessible=true"

# Définir explicitement les variables d'environnement Python pour PySpark
export PYSPARK_PYTHON=python3
export PYSPARK_DRIVER_PYTHON=python3

export PYSPARK_SUBMIT_ARGS="--master ${SPARK_MASTER} --conf spark.executorEnv.PYSPARK_PYTHON=python3 --conf spark.driver.extraJavaOptions=\"${JAVA_OPTS}\" pyspark-shell"

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

# Attendre au moins 10 secondes pour laisser le temps à hdfs-loader de démarrer
echo "Attente de 10 secondes pour laisser le temps à hdfs-loader de démarrer..."
sleep 10

# Si la vérification échoue, le script s'arrêtera ici

# Exécuter le script d'importation
echo "Démarrage de l'importation des données géographiques..."
python /app/geojson_processing.py

echo "Importation terminée."