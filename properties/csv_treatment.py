#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'importation des données immobilières DVF (Demandes de Valeurs Foncières)
Utilise Apache Spark pour traiter les fichiers CSV volumineux et les importer en PostgreSQL
"""

import os
import time
import socket
import logging
import psycopg2
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import DoubleType, DateType, StringType

logging.basicConfig(level=logging.INFO)

# Configuration depuis les variables d'environnement
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

# Attente de la disponibilité de Spark Master
spark_master_host = "spark-master"
spark_master_port = 7077

for i in range(30):
    try:
        socket.create_connection((spark_master_host, spark_master_port), timeout=3).close()
        print("Spark Master prêt!")
        break
    except socket.error:
        print(f"Attente Spark Master, tentative {i+1}/30")
        time.sleep(10)
else:
    raise Exception("Impossible de se connecter à Spark Master")

# Configuration Spark optimisée pour le traitement des données immobilières
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
    """Traite un fichier CSV DVF avec Spark et l'importe en PostgreSQL
    
    Args:
        file_path (str): Chemin vers le fichier CSV à traiter
        
    Returns:
        int: Nombre de lignes insérées
    """
    print(f"Traitement Spark optimisé du fichier: {file_path}")
    
    try:
        # Configuration de la connexion PostgreSQL via JDBC
        postgres_properties = {
            "user": POSTGRES_USER,
            "password": POSTGRES_PASSWORD,
            "driver": "org.postgresql.Driver",
            "batchsize": "10000",
            "isolationLevel": "READ_COMMITTED"
        }
        postgres_url = f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        
        # Lecture du CSV avec inférence automatique du schéma
        print("Lecture du fichier CSV avec Spark...")
        df = spark.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .option("multiline", "true") \
            .option("escape", '"') \
            .csv(file_path)
        
        print("Fichier CSV lu avec succès")
        
        # Filtrage des données valides (latitude, longitude, IDs obligatoires)
        print("Filtrage des données valides...")
        df_clean = df.filter(
            col("latitude").isNotNull() & 
            col("longitude").isNotNull() &
            col("id_mutation").isNotNull() &
            col("id_parcelle").isNotNull()
        )
        
        # Sélection et typage des colonnes pour la table properties
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
        
        # Repartitionnement pour optimiser l'écriture parallèle
        print("Optimisation des partitions...")
        df_partitioned = df_selected.repartition(2)  # 2 partitions pour 2 workers
        
        # Écriture vers table temporaire via Spark JDBC
        print("Écriture vers PostgreSQL avec Spark JDBC...")
        
        # Table temporaire pour l'import en lot
        temp_table = "temp_properties_import"
        
        # Écriture distribuée sans collecte en mémoire
        df_partitioned.write \
            .mode("overwrite") \
            .option("driver", "org.postgresql.Driver") \
            .option("user", POSTGRES_USER) \
            .option("password", POSTGRES_PASSWORD) \
            .option("batchsize", "10000") \
            .option("numPartitions", "2") \
            .jdbc(postgres_url, temp_table, properties=postgres_properties)
        
        print("Données écrites dans table temporaire")
        
        # Transfert vers table finale avec création des géométries PostGIS
        print("Insertion finale avec géométrie PostGIS...")
        
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cursor = conn.cursor()
        
        # Insertion finale avec déduplication et création des points géographiques
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
        
        # Suppression de la table temporaire
        cursor.execute(f"DROP TABLE IF EXISTS {temp_table};")
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return inserted_count
        
    except Exception as e:
        print(f"Erreur traitement Spark: {e}")
        return 0

# Traitement principal des fichiers CSV DVF
print(f"Démarrage du traitement Spark des fichiers DVF")

total_inserted = 0

# Traitement séquentiel de tous les fichiers CSV du répertoire
for filename in os.listdir(CSV_PATH):
    if filename.endswith('.csv'):
        file_path = os.path.join(CSV_PATH, filename)
        print(f"Traitement Spark PUR du fichier: {filename}")
        
        try:
            inserted = process_csv_with_spark_optimized(file_path)
            total_inserted += inserted
                
        except Exception as e:
            print(f"Erreur lors du traitement de {filename}: {e}")
            continue

print(f"Import terminé: {total_inserted} propriétés importées")

spark.stop()
print("Session Spark fermée")
