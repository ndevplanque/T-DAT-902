#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import socket
import logging
import psycopg2
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import DoubleType, DateType
from pyspark.sql import SparkSession

# Configuration logging
logging.basicConfig(level=logging.INFO)

# Variables d'environnement
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')

SPARK_APP_NAME = os.getenv('SPARK_APP_NAME', 'Property_Import')
SPARK_MASTER = os.getenv('SPARK_MASTER', 'spark://spark-master:7077')
SPARK_JARS = os.getenv('SPARK_JARS', '/opt/bitnami/spark/custom-jars/postgresql-42.7.4.jar')
CSV_PATH = os.getenv('CSV_DVF_PATH', '/properties/CSV_DVF')

print("Vérification contenu CSV_PATH dans le conteneur :")
print(os.listdir(CSV_PATH))

# Attente de Spark Master (si nécessaire)
spark_master_host = "spark-master"
spark_master_port = 7077

spark = SparkSession.builder \
    .appName("test") \
    .master("spark://spark-master:7077") \
    .getOrCreate()

print("Spark OK !")

for i in range(30):
    try:
        socket.create_connection((spark_master_host, spark_master_port), timeout=3).close()
        print("Spark Master prêt!")
        break
    except socket.error:
        print(f"Spark Master pas prêt, tentative {i+1}/10")
        time.sleep(10)
else:
    raise Exception("Spark Master n'est pas accessible après plusieurs tentatives.")

# Spark Session
spark = SparkSession.builder \
    .appName(SPARK_APP_NAME) \
    .master(SPARK_MASTER) \
    .config("spark.jars", SPARK_JARS) \
    .config("spark.driver.memory", "2g") \
    .config("spark.executor.memory", "1g") \
    .getOrCreate()

print("CSV_PATH =", CSV_PATH)
print("Contenu du dossier :", os.listdir(CSV_PATH))

# Lecture des fichiers CSV
df = spark.read.csv(f"{CSV_PATH}/*.csv", header=True, sep=",", inferSchema=True)
print(f"{df.count()} lignes lues depuis les CSV.")

# Nettoyage de base
df = df.dropna(subset=["valeur_fonciere", "code_postal", "code_commune", "id_parcelle", "latitude", "longitude"])
df = df.dropDuplicates()

# Casting des types
df = df.withColumn("date_mutation", col("date_mutation").cast(DateType()))
df = df.withColumn("valeur_fonciere", col("valeur_fonciere").cast(DoubleType()))
df = df.withColumn("surface_reelle_bati", col("surface_reelle_bati").cast(DoubleType()))
df = df.withColumn("surface_terrain", col("surface_terrain").cast(DoubleType()))
df = df.withColumn("latitude", col("latitude").cast(DoubleType()))
df = df.withColumn("longitude", col("longitude").cast(DoubleType()))

# Insertion des données dans PostgreSQL avec géométrie
def insert_data(df):
    BATCH_SIZE = 1000
    batch = []

    with psycopg2.connect(
        host=POSTGRES_HOST, port=POSTGRES_PORT, database=POSTGRES_DB,
        user=POSTGRES_USER, password=POSTGRES_PASSWORD
    ) as conn:
        conn.autocommit = True
        with conn.cursor() as cursor:
            for row in df.toLocalIterator():
                try:
                    lat = float(row['latitude']) if row['latitude'] else None
                    lon = float(row['longitude']) if row['longitude'] else None

                    if lat is None or lon is None:
                        continue  # Ignore si coordonnées manquantes

                    batch.append((
                        row['id_mutation'],
                        row['date_mutation'],
                        float(row['valeur_fonciere']) if row['valeur_fonciere'] else None,
                        row['code_postal'],
                        row['code_commune'],
                        row['nom_commune'],
                        row['id_parcelle'],
                        float(row['surface_reelle_bati']) if row['surface_reelle_bati'] else None,
                        float(row['surface_terrain']) if row['surface_terrain'] else None,
                        lon,
                        lat
                    ))
                except Exception as e:
                    print(f"Erreur insertion ligne : {e}")
                    continue

                if len(batch) >= BATCH_SIZE:
                    cursor.executemany("""
                        INSERT INTO properties (
                            id_mutation,
                            date_mutation,
                            valeur_fonciere,
                            code_postal,
                            code_commune,
                            nom_commune,
                            id_parcelle,
                            surface_reelle_bati,
                            surface_terrain,
                            geom
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                                ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                        ON CONFLICT (id_mutation, id_parcelle) DO NOTHING
                    """, batch)
                    print(f"{len(batch)} lignes insérées (batch).")
                    batch.clear()

            # Dernier batch
            if batch:
                cursor.executemany("""
                    INSERT INTO properties (
                        id_mutation,
                        date_mutation,
                        valeur_fonciere,
                        code_postal,
                        code_commune,
                        nom_commune,
                        id_parcelle,
                        surface_reelle_bati,
                        surface_terrain,
                        geom
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                            ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                    ON CONFLICT (id_mutation, id_parcelle) DO NOTHING
                """, batch)
                print(f"{len(batch)} lignes insérées (final batch).")

# Lancer l'insertion
insert_data(df)