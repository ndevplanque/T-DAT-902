import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, col, udf
from pyspark.sql.types import StringType
from shapely.geometry import shape, MultiPolygon, Polygon
import psycopg2
import time
import socket
import sys
# Afficher la version Python du driver
print(f"Driver Python version: {sys.version}")

# Utiliser la même version de Python partout
os.environ['PYSPARK_PYTHON'] = 'python3'
os.environ['PYSPARK_DRIVER_PYTHON'] = 'python3'

# -------------------------
# Chargement des paramètres depuis l'environnement du docker
# -------------------------
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')

SPARK_APP_NAME = os.getenv('SPARK_APP_NAME', 'GeoJSON_Import')
SPARK_MASTER = os.getenv('SPARK_MASTER', 'local[*]')
SPARK_JARS = os.getenv('SPARK_JARS')

HDFS_CITIES_PATH = os.getenv('HDFS_CITIES_PATH')
HDFS_DEPARTMENTS_PATH = os.getenv('HDFS_DEPARTMENTS_PATH')
HDFS_REGIONS_PATH = os.getenv('HDFS_REGIONS_PATH')

print("Attente du démarrage de Spark Master...")
spark_master_host = "spark-master"
spark_master_port = 7077
max_retries = 10

for i in range(max_retries):
    try:
        socket_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_connection.settimeout(3)
        socket_connection.connect((spark_master_host, spark_master_port))
        socket_connection.close()
        print("Spark Master est prêt!")
        break
    except:
        print(f"Tentative {i+1}/{max_retries}: Spark Master n'est pas encore prêt, attente de 10 secondes...")
        time.sleep(10)
    if i == max_retries - 1:
        print("Échec de connexion à Spark Master après plusieurs tentatives")

# -------------------------
# Création de la session Spark avec les configurations externes
# -------------------------

# Utiliser le cluster Spark
print("Création de la session Spark en mode cluster...")
try:
    spark = SparkSession.builder \
        .appName(SPARK_APP_NAME) \
        .master(SPARK_MASTER) \
        .config("spark.jars", SPARK_JARS) \
        .config("spark.driver.memory", "2g") \
        .config("spark.executor.memory", "1g") \
        .config("spark.cores.max", "2") \
        .config("spark.executorEnv.PYSPARK_PYTHON", "python3") \
        .getOrCreate()

    print(f"Session Spark créée avec succès sur le master: {SPARK_MASTER}")

    # Afficher des informations sur le cluster
    print("Configuration du cluster Spark:")
    print(f"Version de Spark: {spark.version}")
    print(f"Master: {spark.sparkContext.master}")
    print(f"Nombre d'exécuteurs disponibles: {spark.sparkContext.defaultParallelism}")
except Exception as e:
    print(f"Erreur lors de la création de la session Spark: {e}")
    exit(1)

print("Spark session created successfully!")

# -------------------------
# Fonctions de nettoyage et de conversion de géométrie
# -------------------------
def parse_coordinate_string(s):
    """
    Convertit une chaîne de type "[-61.549,16.253]"
    en une liste de deux floats. Gère le cas où le séparateur décimal est mal placé.
    """
    s_clean = s.strip("[]")
    parts = [p.strip() for p in s_clean.split(',')]
    if len(parts) == 2:
        return [float(parts[0]), float(parts[1])]
    else:
        raise ValueError(f"Format de coordonnée inattendu : {s}")

def clean_coords(coords):
    """
    Parcourt récursivement la structure des coordonnées et convertit
    les chaînes de coordonnées mal formatées en listes de floats.
    """
    if isinstance(coords, list):
        new_coords = []
        for item in coords:
            if isinstance(item, list):
                new_coords.append(clean_coords(item))
            elif isinstance(item, str):
                if item.startswith('['):
                    new_coords.append(parse_coordinate_string(item))
                else:
                    try:
                        new_coords.append(float(item))
                    except ValueError:
                        new_coords.append(item)
            else:
                new_coords.append(item)
        return new_coords
    else:
        return coords

def geojson_to_wkt(geometry_row):
    """
    Convertit une géométrie GeoJSON en sa représentation WKT.
    Corrige la géométrie si nécessaire.
    """
    if geometry_row is None:
        return None
    try:
        # Convertir le Row en dictionnaire
        geometry_dict = geometry_row.asDict()

        # Nettoyage des coordonnées pour MultiPolygon
        if geometry_dict.get("type") == "MultiPolygon":
            geometry_dict["coordinates"] = clean_coords(geometry_dict["coordinates"])

        # Création de l'objet Shapely à partir du dictionnaire GeoJSON
        shapely_geom = shape(geometry_dict)

        # Correction de la validité de la géométrie si nécessaire
        if not shapely_geom.is_valid:
            shapely_geom = shapely_geom.buffer(0)

        # Transformation d'un Polygon en MultiPolygon
        if isinstance(shapely_geom, Polygon):
            shapely_geom = MultiPolygon([shapely_geom])

        # Retourne la représentation WKT de la géométrie
        return shapely_geom.wkt
    except Exception as e:
        print(f"Erreur lors de la conversion de la géométrie : {e}")
        exit()
        return None

# Déclaration de l'UDF PySpark pour la conversion en WKT
geometry_to_wkt_udf = udf(geojson_to_wkt, StringType())

# -------------------------
# Importation des données GeoJSON depuis HDFS
# -------------------------
# Importation des communes (cities)
df_raw_cities = spark.read.json(HDFS_CITIES_PATH)
df_features_cities = df_raw_cities.select(explode(col("features")).alias("feature"))
df_cities = df_features_cities.select(
    col("feature.properties.code").alias("city_id"),
    col("feature.properties.nom").alias("name"),
    col("feature.properties.departement").alias("department_id"),
    col("feature.properties.region").alias("region_id"),
    col("feature.geometry").alias("geometry")
)
df_cities = df_cities.withColumn("geom", geometry_to_wkt_udf(col("geometry"))) \
    .select("city_id", "name", "department_id", "region_id", "geom")

# Importation des départements
df_raw_depts = spark.read.json(HDFS_DEPARTMENTS_PATH)
df_features_depts = df_raw_depts.select(explode(col("features")).alias("feature"))
df_departments = df_features_depts.select(
    col("feature.properties.code").alias("department_id"),
    col("feature.properties.nom").alias("name"),
    col("feature.properties.region").alias("region_id"),
    col("feature.geometry").alias("geometry")
)
df_departments = df_departments.withColumn("geom", geometry_to_wkt_udf(col("geometry"))) \
    .select("department_id", "name", "region_id", "geom")

# Importation des régions
df_raw_regions = spark.read.json(HDFS_REGIONS_PATH)
df_features_regions = df_raw_regions.select(explode(col("features")).alias("feature"))
df_regions = df_features_regions.select(
    col("feature.properties.code").alias("region_id"),
    col("feature.properties.nom").alias("name"),
    col("feature.geometry").alias("geometry")
)
df_regions = df_regions.withColumn("geom", geometry_to_wkt_udf(col("geometry"))) \
    .select("region_id", "name", "geom")

# Code pour le partitionnement
print("Configuration du partitionnement des données pour le traitement distribué...")
num_partitions = 4  # Ou un nombre approprié pour vos données

# Repartitionner les DataFrames
df_cities = df_cities.repartition(num_partitions)
df_departments = df_departments.repartition(num_partitions)
df_regions = df_regions.repartition(num_partitions)

# Contrôler explicitement l'exécution
spark.conf.set("spark.sql.shuffle.partitions", num_partitions)
print(f"Données repartitionnées en {num_partitions} partitions")

# -------------------------
# Fonctions d'insertion dans PostgreSQL via foreachPartition
# -------------------------
def insert_partition_cities(rows):
    # Connexion à PostgreSQL avec les paramètres externes
    conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    )
    cur = conn.cursor()
    sql = """
        INSERT INTO cities (city_id, name, department_id, region_id, geom)
        VALUES (%s, %s, %s, %s, ST_GeomFromText(%s, 4326))
        ON CONFLICT (city_id) DO UPDATE SET geom = EXCLUDED.geom;
    """
    for row in rows:
        if row.geom is None:
            continue
        cur.execute(sql, (row.city_id, row.name, row.department_id, row.region_id, row.geom))
    conn.commit()
    cur.close()
    conn.close()

def insert_partition_departments(rows):
    conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    )
    cur = conn.cursor()
    sql = """
        INSERT INTO departments (department_id, name, region_id, geom)
        VALUES (%s, %s, %s, ST_GeomFromText(%s, 4326))
        ON CONFLICT (department_id) DO UPDATE SET geom = EXCLUDED.geom;
    """
    for row in rows:
        if row.geom is None:
            continue
        cur.execute(sql, (row.department_id, row.name, row.region_id, row.geom))
    conn.commit()
    cur.close()
    conn.close()

def insert_partition_regions(rows):
    conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    )
    cur = conn.cursor()
    sql = """
        INSERT INTO regions (region_id, name, geom)
        VALUES (%s, %s, ST_GeomFromText(%s, 4326))
        ON CONFLICT (region_id) DO UPDATE SET geom = EXCLUDED.geom;
    """
    for row in rows:
        if row.geom is None:
            continue
        cur.execute(sql, (row.region_id, row.name, row.geom))
    conn.commit()
    cur.close()
    conn.close()

# -------------------------
# Insertion des données dans PostgreSQL
# -------------------------
df_regions.foreachPartition(insert_partition_regions)
df_departments.foreachPartition(insert_partition_departments)
df_cities.foreachPartition(insert_partition_cities)

spark.stop()