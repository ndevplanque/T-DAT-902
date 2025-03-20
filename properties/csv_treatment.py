#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script d'importation de données immobilières depuis plusieurs fichiers CSV
d'un dossier vers PostgreSQL en utilisant PySpark avec support pour la géolocalisation.
Filtrage sur les ventes de maisons et appartements uniquement.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, concat_ws, regexp_replace, when, lit, to_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType
import os
from datetime import datetime
import glob
from pyspark import SparkFiles

# Configuration des paramètres de connexion à PostgreSQL
POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'gis_db') 
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'postgres')

# Dossier contenant les fichiers CSV
CSV_FOLDER = "/app/CSV_DVF/" # Dossier contenant les fichiers CSV

def create_spark_session():
    """Création et configuration de la session Spark avec les dépendances nécessaires."""
    spark_master = os.environ.get('SPARK_MASTER', 'spark://spark-master:7077')
    
    # Chercher le JAR dans le dossier monté
    jar_path = "/opt/bitnami/spark/custom-jars/postgresql-42.7.4.jar"
    
    # Vérification que le JAR existe
    if not os.path.exists(jar_path):
        print(f"ERREUR: Le JAR PostgreSQL n'existe pas à l'emplacement {jar_path}")
        # Essayer des alternatives
        alternatives = [
            "/jars/postgresql-42.6.0.jar",
            "/app/jars/postgresql-42.6.0.jar",
            "/app/jars/postgresql-42.7.4.jar"
        ]
        for alt in alternatives:
            if os.path.exists(alt):
                jar_path = alt
                print(f"JAR PostgreSQL trouvé à {jar_path}")
                break
    
    print(f"Utilisation du JAR : {jar_path}")
    return (SparkSession.builder
            .appName("ImportationDonneesImmobilieres")
            .master(spark_master)
            .config("spark.jars", jar_path)
            # Ajout de configurations pour distribuer les tâches
            .config("spark.submit.deployMode", "client")
            .config("spark.executor.instances", "2")
            .config("spark.executor.cores", "1")
            .config("spark.executor.memory", "1g")
            .getOrCreate())

# Définition du schéma du CSV pour éviter l'inférence automatique
def get_schema():
    """Retourne le schéma des fichiers CSV."""
    return StructType([
        StructField("id_mutation", StringType(), True),
        StructField("date_mutation", StringType(), True),
        StructField("numero_disposition", StringType(), True),
        StructField("nature_mutation", StringType(), True),
        StructField("valeur_fonciere", StringType(), True),
        StructField("adresse_numero", StringType(), True),
        StructField("adresse_suffixe", StringType(), True),
        StructField("adresse_code_voie", StringType(), True),
        StructField("adresse_nom_voie", StringType(), True),
        StructField("code_postal", StringType(), True),
        StructField("code_commune", StringType(), True),
        StructField("nom_commune", StringType(), True),
        StructField("ancien_code_commune", StringType(), True),
        StructField("ancien_nom_commune", StringType(), True),
        StructField("code_departement", StringType(), True),
        StructField("id_parcelle", StringType(), True),
        StructField("ancien_id_parcelle", StringType(), True),
        StructField("numero_volume", StringType(), True),
        StructField("lot_1_numero", StringType(), True),
        StructField("lot_1_surface_carrez", StringType(), True),
        StructField("lot_2_numero", StringType(), True),
        StructField("lot_2_surface_carrez", StringType(), True),
        StructField("lot_3_numero", StringType(), True),
        StructField("lot_3_surface_carrez", StringType(), True),
        StructField("lot_4_numero", StringType(), True),
        StructField("lot_4_surface_carrez", StringType(), True),
        StructField("lot_5_numero", StringType(), True),
        StructField("lot_5_surface_carrez", StringType(), True),
        StructField("nombre_lots", StringType(), True),
        StructField("code_type_local", StringType(), True),
        StructField("type_local", StringType(), True),
        StructField("surface_reelle_bati", StringType(), True),
        StructField("nombre_pieces_principales", StringType(), True),
        StructField("code_nature_culture", StringType(), True),
        StructField("nature_culture", StringType(), True),
        StructField("code_nature_culture_speciale", StringType(), True),
        StructField("nature_culture_speciale", StringType(), True),
        StructField("surface_terrain", StringType(), True),
        StructField("longitude", StringType(), True),
        StructField("latitude", StringType(), True)
    ])

def process_csv_file(spark, file_path):
    """Traite un fichier CSV et retourne un DataFrame avec les transformations appliquées."""
    print(f"Lecture du fichier: {file_path}...")
    

    # Lecture du fichier CSV
    df = spark.read.option("header", "true") \
                   .option("delimiter", ",") \
                   .option("encoding", "UTF-8") \
                   .schema(get_schema()) \
                   .csv(file_path)
    
    # Filtrage des données pour ne conserver que les ventes de maisons et appartements
    df = df.filter(
        (col("nature_mutation") == "Vente") & 
        ((col("type_local") == "Maison") | (col("type_local") == "Appartement"))
    )
    
    # Transformation des données pour correspondre au schéma de la table PostgreSQL
    properties_df = df.select(
        # Création de l'adresse complète
        concat_ws(" ", 
            col("adresse_numero"), 
            col("adresse_suffixe"),
            col("adresse_nom_voie")
        ).alias("property_address"),
        
        # Prix (valeur_fonciere) - conversion en type numérique
        col("valeur_fonciere").cast(DoubleType()).alias("price"),
        
        # Surface - utilisation de la surface réelle du bâti
        col("surface_reelle_bati").cast(DoubleType()).alias("surface"),
        
        # Nombre de pièces
        col("nombre_pieces_principales").cast(IntegerType()).alias("rooms"),
        
        # Clé étrangère vers la table cities - utilisation du code_commune
        col("code_commune").alias("city_id"),
        
        # Date de vente
        to_timestamp(col("date_mutation"), "yyyy-MM-dd").alias("sell_date"),
        
        # Coordonnées géographiques
        col("longitude").cast(DoubleType()),
        col("latitude").cast(DoubleType())
    )
    
    # Filtrage des données nulles ou invalides
    properties_df = properties_df.filter(
        (col("price").isNotNull()) & 
        (col("surface").isNotNull()) & 
        (col("rooms").isNotNull()) & 
        (col("property_address").isNotNull()) &
        (col("city_id").isNotNull()) &
        (col("sell_date").isNotNull()) &
        (col("longitude").isNotNull()) &
        (col("latitude").isNotNull())
    )
    
    return properties_df

def setup_database():
    """Configure la base de données et crée la table properties."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        
        with conn.cursor() as cursor:
            # Vérification si la table cities existe
            cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'cities'
            );
            """)
            cities_table_exists = cursor.fetchone()[0]
            
            if not cities_table_exists:
                print("ATTENTION: La table 'cities' n'existe pas. Il faudra créer cette table avant l'importation ou supprimer la contrainte de clé étrangère.")
                
            # Création du schéma de la table properties selon les spécifications exactes
            cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            
            # Création de la table finale si elle n'existe pas
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                property_id SERIAL PRIMARY KEY,
                price NUMERIC,
                surface NUMERIC,
                rooms INTEGER,
                property_address TEXT,
                city_id VARCHAR(10),
                sell_date TIMESTAMP,
                geom GEOMETRY(POINT, 4326)
            );
            """)
            
            # Ajout de la contrainte de clé étrangère si la table cities existe et si la contrainte n'existe pas déjà
            if cities_table_exists:
                # Vérifier si la contrainte existe déjà
                cursor.execute("""
                SELECT COUNT(*) FROM pg_constraint 
                WHERE conname = 'fk_city_id' AND conrelid = 'properties'::regclass;
                """)
                constraint_exists = cursor.fetchone()[0] > 0
                
                if not constraint_exists:
                    cursor.execute("""
                    ALTER TABLE properties 
                    ADD CONSTRAINT fk_city_id 
                    FOREIGN KEY (city_id) 
                    REFERENCES cities(city_id);
                    """)
            
            conn.commit()
            print("Structure de la table vérifiée/créée avec succès dans PostgreSQL.")
        
        return True
    except Exception as e:
        print(f"Erreur lors de la configuration de la base de données: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def insert_data_to_postgres(df):
    """Insère les données du DataFrame dans PostgreSQL."""
    if df.count() == 0:
        print("Aucune donnée à insérer.")
        return 0
        
    # URL de connexion JDBC pour PostgreSQL
    jdbc_url = f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # Propriétés de connexion
    connection_properties = {
        "user": POSTGRES_USER,
        "password": POSTGRES_PASSWORD,
        "driver": "org.postgresql.Driver"
    }
    
    try:
        # Connexion à PostgreSQL
        import psycopg2
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        
        # Création d'une table temporaire pour les données
        with conn.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS properties_temp;")
            cursor.execute("""
            CREATE TABLE properties_temp (
                property_id SERIAL PRIMARY KEY,
                price NUMERIC,
                surface NUMERIC,
                rooms INTEGER,
                property_address TEXT,
                city_id VARCHAR(10),
                sell_date TIMESTAMP,
                longitude DOUBLE PRECISION,
                latitude DOUBLE PRECISION
            );
            """)
            conn.commit()
        
        # Insertion des données dans la table temporaire
        df.write.jdbc(jdbc_url, "properties_temp", mode="append", properties=connection_properties)
        
        # Transfert des données vers la table finale avec création de la géométrie
        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO properties (price, surface, rooms, property_address, city_id, sell_date, geom)
            SELECT 
                price, 
                surface, 
                rooms, 
                property_address, 
                city_id, 
                sell_date, 
                ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) as geom
            FROM properties_temp;
            """)
            
            # Récupération du nombre d'enregistrements insérés
            cursor.execute("SELECT COUNT(*) FROM properties WHERE property_id > (SELECT COALESCE(MAX(property_id), 0) FROM properties) - (SELECT COUNT(*) FROM properties_temp);")
            count_inserted = cursor.fetchone()[0]
            
            # Nettoyage de la table temporaire
            cursor.execute("DROP TABLE properties_temp;")
            conn.commit()
        
        return count_inserted
    
    except Exception as e:
        print(f"Erreur lors de l'insertion des données: {e}")
        return 0
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Fonction principale du script."""
    # Création de la session Spark
    spark = create_spark_session()
    
    # Configuration de la base de données
    if not setup_database():
        print("Impossible de configurer la base de données. Arrêt du script.")
        return
    
    # Recherche des fichiers CSV dans le dossier spécifié
    csv_files = glob.glob(os.path.join(CSV_FOLDER, "*.csv"))
    
    if not csv_files:
        print(f"Aucun fichier CSV trouvé dans le dossier '{CSV_FOLDER}'.")
        return
    
    print(f"Nombre de fichiers CSV trouvés: {len(csv_files)}")
    print(f"Fichiers: {csv_files}")
    
    # Variables pour les statistiques
    total_processed = 0
    total_inserted = 0
    
    # Traitement de chaque fichier CSV
    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        print(f"\nTraitement du fichier: {file_name}")
        
        if not os.path.exists(file_path):
            print(f"AVERTISSEMENT: Le fichier {file_path} n'existe pas!")
            continue
            
        # Traiter le fichier CSV
        try:
            properties_df = process_csv_file(spark, file_path)
            
            # Affichage du nombre de lignes après traitement
            row_count = properties_df.count()
            print(f"Nombre d'enregistrements valides: {row_count}")
            total_processed += row_count
            
            # Insertion des données dans PostgreSQL
            if row_count > 0:
                inserted_count = insert_data_to_postgres(properties_df)
                print(f"Nombre d'enregistrements insérés: {inserted_count}")
                total_inserted += inserted_count
        except Exception as e:
            print(f"Erreur lors du traitement du fichier {file_name}: {e}")

if __name__ == "__main__":
    main()