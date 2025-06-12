#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import socket
import logging
import psycopg2
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, isnan, isnull
from pyspark.sql.types import DoubleType, DateType, StringType

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

# Attente de Spark Master
spark_master_host = "spark-master"
spark_master_port = 7077

for i in range(30):
    try:
        socket.create_connection((spark_master_host, spark_master_port), timeout=3).close()
        print("Spark Master prêt!")
        break
    except socket.error:
        print(f"Spark Master pas prêt, tentative {i+1}/30")
        time.sleep(10)
else:
    raise Exception("Spark Master n'est pas accessible après plusieurs tentatives.")

# Configuration Spark optimisée et stable
spark = SparkSession.builder \
    .appName(SPARK_APP_NAME) \
    .master(SPARK_MASTER) \
    .config("spark.jars", SPARK_JARS) \
    .config("spark.driver.memory", "3g") \
    .config("spark.executor.memory", "6g") \
    .config("spark.driver.maxResultSize", "2g") \
    .config("spark.sql.adaptive.enabled", "false") \
    .config("spark.sql.adaptive.coalescePartitions.enabled", "false") \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .config("spark.sql.shuffle.partitions", "4") \
    .config("spark.default.parallelism", "1") \
    .config("spark.sql.adaptive.advisoryPartitionSizeInBytes", "32MB") \
    .config("spark.pyspark.python", "/opt/bitnami/python/bin/python3") \
    .config("spark.pyspark.driver.python", "/usr/local/bin/python") \
    .config("spark.dynamicAllocation.enabled", "false") \
    .config("spark.network.timeout", "800s") \
    .config("spark.executor.heartbeatInterval", "60s") \
    .config("spark.sql.execution.arrow.pyspark.enabled", "false") \
    .config("spark.executor.extraJavaOptions", "-XX:+UseG1GC") \
    .config("spark.driver.extraJavaOptions", "-XX:+UseG1GC") \
    .getOrCreate()

print("Spark Session créée avec succès !")

print("CSV_PATH =", CSV_PATH)
print("Contenu du dossier :", os.listdir(CSV_PATH))

def process_csv_with_spark_optimized(file_path):
    """Traite un fichier CSV avec Spark optimisé pour gros volumes"""
    print(f"Traitement Spark optimisé du fichier: {file_path}")
    
    try:
        # Configuration PostgreSQL pour JDBC
        postgres_properties = {
            "user": POSTGRES_USER,
            "password": POSTGRES_PASSWORD,
            "driver": "org.postgresql.Driver",
            "batchsize": "10000",
            "isolationLevel": "READ_COMMITTED"
        }
        postgres_url = f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        
        # Lecture optimisée avec inférence de schéma
        print("Lecture du fichier CSV avec Spark...")
        df = spark.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .option("multiline", "true") \
            .option("escape", '"') \
            .csv(file_path)
        
        print("Fichier CSV lu avec succès")
        
        # Filtrage et nettoyage AVANT les transformations coûteuses
        print("Filtrage des données valides...")
        df_clean = df.filter(
            col("latitude").isNotNull() & 
            col("longitude").isNotNull() &
            col("id_mutation").isNotNull() &
            col("id_parcelle").isNotNull()
        )
        
        # Sélection des colonnes nécessaires seulement
        print("Sélection des colonnes...")
        df_selected = df_clean.select(
            col("id_mutation").cast(StringType()),
            col("date_mutation").cast(DateType()),
            col("valeur_fonciere").cast(DoubleType()),
            col("code_postal").cast(StringType()),
            col("code_commune").cast(StringType()),
            col("nom_commune").cast(StringType()),
            col("id_parcelle").cast(StringType()),
            col("surface_reelle_bati").cast(DoubleType()),
            col("surface_terrain").cast(DoubleType()),
            col("latitude").cast(DoubleType()),
            col("longitude").cast(DoubleType())
        )
        
        # Optimisation des partitions AVANT écriture
        print("Optimisation des partitions...")
        df_partitioned = df_selected.repartition(2)  # 2 partitions pour 2 workers
        
        # Écriture directe vers table temporaire avec Spark JDBC
        print("Écriture vers PostgreSQL avec Spark JDBC...")
        
        # Créer table temporaire d'abord
        temp_table = "temp_properties_import"
        
        # Écriture Spark JDBC directe (sans collect)
        df_partitioned.write \
            .mode("overwrite") \
            .option("driver", "org.postgresql.Driver") \
            .option("user", POSTGRES_USER) \
            .option("password", POSTGRES_PASSWORD) \
            .option("batchsize", "10000") \
            .option("numPartitions", "2") \
            .jdbc(postgres_url, temp_table, properties=postgres_properties)
        
        print("Données écrites dans table temporaire")
        
        # Insertion finale avec géométrie via PostgreSQL
        print("Insertion finale avec géométrie PostGIS...")
        
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cursor = conn.cursor()
        
        # Insertion avec déduplication et géométrie
        insert_sql = f"""
        INSERT INTO properties (
            id_mutation, date_mutation, valeur_fonciere, code_postal,
            code_commune, nom_commune, id_parcelle, surface_reelle_bati,
            surface_terrain, geom
        )
        SELECT DISTINCT
            id_mutation, date_mutation, valeur_fonciere, code_postal,
            code_commune, nom_commune, id_parcelle, surface_reelle_bati,
            surface_terrain,
            ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) as geom
        FROM {temp_table}
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ON CONFLICT (id_mutation, id_parcelle) DO NOTHING;
        """
        
        cursor.execute(insert_sql)
        inserted_count = cursor.rowcount
        conn.commit()
        
        print(f"{inserted_count} lignes insérées dans properties")
        
        # Nettoyage
        cursor.execute(f"DROP TABLE IF EXISTS {temp_table};")
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return inserted_count
        
    except Exception as e:
        print(f"Erreur traitement Spark: {e}")
        return 0

# TRAITEMENT PRINCIPAL AVEC SPARK PUR
print(f"Traitement des fichiers CSV avec Apache Spark PUR (sans pandas/psycopg2)")

total_inserted = 0

# Traitement de tous les fichiers CSV du dossier avec Spark
for filename in os.listdir(CSV_PATH):
    if filename.endswith('.csv'):
        file_path = os.path.join(CSV_PATH, filename)
        print(f"Traitement Spark PUR du fichier: {filename}")
        
        try:
            # Traitement avec Spark optimisé
            inserted = process_csv_with_spark_optimized(file_path)
            total_inserted += inserted
                
        except Exception as e:
            print(f"Erreur traitement Spark PUR fichier {filename}: {e}")
            continue

print(f"Traitement Spark PUR terminé: {total_inserted} lignes insérées au total")

# Fermeture de la session Spark
spark.stop()
print("Session Spark fermée")
