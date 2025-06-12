# Properties Importer - Service d'importation immobilière DVF

## Vue d'ensemble

Le service **properties-importer** constitue le moteur de traitement des données immobilières DVF (Demandes de Valeurs Foncières) de Homepedia. Il utilise Apache Spark pour traiter efficacement de gros volumes de transactions immobilières françaises (1,5M transactions, 260MB) et les intégrer dans PostgreSQL avec des capacités géospatiales PostGIS.

## Architecture du service

### Responsabilités principales

1. **Import massif**: Traitement de fichiers CSV DVF volumineux via Spark
2. **Validation géospatiale**: Nettoyage et validation des coordonnées GPS
3. **Déduplication**: Élimination des doublons basée sur clés composites
4. **Géolocalisation**: Création de géométries PostGIS à partir de coordonnées
5. **Optimisation**: Configuration mémoire et parallélisme pour performance

### Technologies utilisées

- **Apache Spark 3.4.1**: Traitement distribué des données
- **PostgreSQL + PostGIS**: Base géospatiale finale
- **Python 3.11**: Runtime et traitement
- **Docker**: Conteneurisation avec limites mémoire
- **JDBC**: Connectivité Spark-PostgreSQL

## Configuration Docker

### Container principal

```yaml
properties-importer:
  build:
    context: ./properties
  container_name: properties-importer
  restart: "no"
  mem_limit: 4g                    # Limite mémoire stricte
  memswap_limit: 4g               # Swap limité pour éviter OOM
  depends_on:
    postgres: { condition: service_healthy }
    spark-master: { condition: service_started }
    spark-worker: { condition: service_started }
    spark-worker-2: { condition: service_started }
    geo-data-importer: { condition: service_completed_successfully }
```

### Variables d'environnement

```bash
# Configuration base de données
POSTGRES_DB=gis_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Configuration Spark
PYSPARK_PYTHON=/opt/bitnami/python/bin/python3
PYSPARK_DRIVER_PYTHON=/usr/local/bin/python
SPARK_MASTER=spark://spark-master:7077
SPARK_APP_NAME=Property_Import
SPARK_JARS=/app/jars/postgresql-42.7.4.jar

# Configuration traitement
CSV_DVF_PATH=/properties/CSV_DVF
CHUNK_SIZE=10000
```

## Données DVF traitées

### Structure du fichier source

**Fichier**: `full_dvf_2025.csv` (260 MB, 1,5M transactions)

**Colonnes principales**:
```
# Identifiants
id_mutation              # Identifiant unique de transaction
id_parcelle              # Identifiant parcelle cadastrale

# Transaction
date_mutation            # Date de la transaction
valeur_fonciere          # Prix de vente (€)
nature_mutation          # Type de transaction

# Localisation administrative
code_commune             # Code INSEE commune
nom_commune              # Nom de la commune
code_postal              # Code postal

# Géolocalisation
latitude                 # Coordonnée GPS latitude WGS84
longitude                # Coordonnée GPS longitude WGS84

# Surfaces
surface_reelle_bati      # Surface bâtie (m²)
surface_terrain          # Surface terrain (m²)
```

### Qualité des données

- **1,5M transactions** au total
- **30,860 villes** avec au moins une transaction
- **0 prix négatif** détecté
- **100% cohérence** spatiale vérifiée
- **22,800 villes** avec prix > 50,000€

## Pipeline de traitement Spark

### Configuration Spark optimisée

```python
# Script csv_treatment.py
spark = SparkSession.builder \
    .appName("Property_Import") \
    .master("spark://spark-master:7077") \
    .config("spark.jars", "/app/jars/postgresql-42.7.4.jar") \
    .config("spark.driver.memory", "3g") \
    .config("spark.executor.memory", "6g") \
    .config("spark.driver.maxResultSize", "2g") \
    .config("spark.sql.shuffle.partitions", "4") \
    .config("spark.default.parallelism", "1") \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .config("spark.executor.extraJavaOptions", "-XX:+UseG1GC") \
    .getOrCreate()
```

### Lecture et validation des données

```python
def load_and_validate_csv(file_path):
    """Charge et valide le fichier CSV DVF avec gestion des erreurs"""
    
    # Lecture avec gestion des caractères spéciaux
    df = spark.read \
        .option("header", "true") \
        .option("inferSchema", "true") \
        .option("multiline", "true") \
        .option("escape", '"') \
        .option("encoding", "UTF-8") \
        .csv(file_path)
    
    # Filtrage des données valides obligatoires
    df_clean = df.filter(
        col("latitude").isNotNull() & 
        col("longitude").isNotNull() &
        col("id_mutation").isNotNull() &
        col("id_parcelle").isNotNull() &
        col("latitude").between(-90, 90) &      # Validation latitude
        col("longitude").between(-180, 180)    # Validation longitude
    )
    
    return df_clean
```

### Transformation et typage

```python
def transform_data_types(df):
    """Applique les types de données appropriés"""
    
    df_transformed = df.select(
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
        col("longitude").cast(DoubleType()),
        col("nature_mutation").cast(StringType())
    )
    
    # Optimisation des partitions pour 2 workers
    return df_transformed.repartition(2)
```

## Intégration PostgreSQL/PostGIS

### Schéma de table principal

```sql
CREATE TABLE IF NOT EXISTS properties (
    id_mutation TEXT NOT NULL,                    -- Clé primaire composite
    id_parcelle TEXT NOT NULL,                    -- Clé primaire composite
    date_mutation DATE,
    valeur_fonciere DOUBLE PRECISION,
    code_postal TEXT,
    code_commune TEXT,
    nom_commune TEXT,
    surface_reelle_bati DOUBLE PRECISION,
    surface_terrain DOUBLE PRECISION,
    nature_mutation TEXT,
    geom geometry(Point, 4326),                   -- Géométrie PostGIS
    
    PRIMARY KEY (id_mutation, id_parcelle)        -- Prévient les doublons
);
```

### Index pour performance

```sql
-- Index spatial pour requêtes géographiques
CREATE INDEX idx_properties_geom ON properties USING GIST (geom);

-- Index sur colonnes fréquemment requêtées
CREATE INDEX idx_properties_code_commune ON properties(code_commune);
CREATE INDEX idx_properties_date_mutation ON properties(date_mutation);
CREATE INDEX idx_properties_valeur_fonciere ON properties(valeur_fonciere);
```

### Import en deux phases

#### Phase 1: Table temporaire via Spark JDBC

```python
def write_to_temp_table(df):
    """Écrit les données dans une table temporaire via JDBC"""
    
    postgres_properties = {
        "user": POSTGRES_USER,
        "password": POSTGRES_PASSWORD,
        "driver": "org.postgresql.Driver",
        "batchsize": "10000",                     # Optimisation batch
        "isolationLevel": "READ_COMMITTED"
    }
    
    df.write \
        .jdbc(jdbc_url, "temp_properties_import", 
              mode="overwrite", properties=postgres_properties)
```

#### Phase 2: Transformation PostGIS + déduplication

```sql
-- Création des géométries et déduplication
INSERT INTO properties (
    id_mutation, date_mutation, valeur_fonciere, code_postal,
    code_commune, nom_commune, id_parcelle, surface_reelle_bati,
    surface_terrain, nature_mutation, geom
)
SELECT DISTINCT
    id_mutation, date_mutation, valeur_fonciere, code_postal,
    code_commune, nom_commune, id_parcelle, surface_reelle_bati,
    surface_terrain, nature_mutation,
    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) as geom
FROM temp_properties_import
WHERE latitude IS NOT NULL 
  AND longitude IS NOT NULL
  AND latitude BETWEEN -90 AND 90
  AND longitude BETWEEN -180 AND 180
ON CONFLICT (id_mutation, id_parcelle) DO NOTHING;
```

## Scripts et orchestration

### Script principal (csv_treatment.py)

```python
def main():
    """Point d'entrée principal du traitement"""
    
    # 1. Initialisation Spark
    spark = create_spark_session()
    
    # 2. Chargement et validation
    df = load_and_validate_csv(CSV_DVF_PATH)
    
    # 3. Transformation
    df_transformed = transform_data_types(df)
    
    # 4. Écriture temporaire
    write_to_temp_table(df_transformed)
    
    # 5. Traitement PostGIS final
    execute_postgis_processing()
    
    # 6. Nettoyage
    cleanup_temp_tables()
```

### Script de soumission Spark

```bash
#!/bin/bash
# spark-submit.sh

echo "Soumission du job Spark pour import des propriétés..."

spark-submit \
    --master spark://spark-master:7077 \
    --deploy-mode client \
    --driver-memory 3g \
    --executor-memory 6g \
    --total-executor-cores 6 \
    --jars /app/jars/postgresql-42.7.4.jar \
    /app/csv_treatment.py

echo "Job Spark terminé"
```

### Attente des dépendances

```bash
#!/bin/bash
# wait-for-postgres.sh

echo "Attente de PostgreSQL..."
until pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER; do
    echo "PostgreSQL non disponible - attente..."
    sleep 2
done
echo "PostgreSQL prêt!"
```

## Géolocalisation et jointures spatiales

### Création des géométries

```sql
-- Conversion coordonnées → géométrie PostGIS
ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) as geom
```

**Paramètres**:
- **SRID 4326**: Système de référence WGS84 (GPS standard)
- **Point geometry**: Type géométrique optimal pour coordonnées ponctuelles
- **Validation intégrée**: PostGIS valide automatiquement les géométries

### Jointures spatiales pour agrégation

```sql
-- Exemple: Propriétés par commune
SELECT 
    c.city_id,
    c.name as commune_name,
    COUNT(p.*) as nb_transactions,
    AVG(p.valeur_fonciere) as prix_moyen,
    ST_Area(c.geom) as superficie_commune
FROM cities c
LEFT JOIN properties p ON ST_Within(p.geom, c.geom)
GROUP BY c.city_id, c.name, c.geom;
```

## Tables d'agrégation créées

Le service properties-importer alimente les tables d'agrégation suivantes:

### 1. properties_cities_stats (30,860 villes)

```sql
CREATE TABLE properties_cities_stats (
    city_id VARCHAR(10) PRIMARY KEY,
    city_name TEXT,
    nb_transactions INTEGER,
    prix_moyen DOUBLE PRECISION,
    prix_median DOUBLE PRECISION,
    prix_min DOUBLE PRECISION,
    prix_max DOUBLE PRECISION,
    prix_m2_moyen DOUBLE PRECISION,
    surface_bati_moyenne DOUBLE PRECISION,
    surface_terrain_moyenne DOUBLE PRECISION,
    premiere_transaction DATE,
    derniere_transaction DATE,
    densite_transactions_km2 DOUBLE PRECISION
);
```

### 2. properties_departments_stats (97 départements)

Agrégation des données par département avec même structure.

### 3. properties_regions_stats (17 régions)

Agrégation des données par région avec même structure.

## Performance et métriques

### Métriques de traitement

- **Données source**: 260 MB, 1,5M transactions
- **Temps de traitement**: ~10-15 minutes
- **Mémoire utilisée**: Max 3.8 GB (sous limite 4GB)
- **Parallélisme**: 2 partitions Spark, 6 cores total
- **Débit**: ~100k transactions/minute

### Statistiques des données

**Prix immobiliers**:
- Prix moyen national: 150,681€
- Prix minimum: 1€
- Prix maximum: 29,7M€
- Médiane nationale: ~120,000€

**Répartition géographique**:
- 30,860 villes avec transactions
- 22,800 villes avec prix > 50,000€
- 97 départements couverts
- 17 régions complètes

### Top villes par volume

1. **Nice**: 4,604 transactions (354k€ moyen)
2. **Toulouse**: 4,430 transactions (291k€ moyen)
3. **Nantes**: 2,672 transactions (294k€ moyen)
4. **Lyon**: 2,445 transactions (385k€ moyen)
5. **Marseille**: 2,234 transactions (245k€ moyen)

## Optimisations et configuration

### Optimisations Spark

1. **G1GC**: Garbage collector optimisé pour gros datasets
2. **KryoSerializer**: Sérialisation binaire haute performance
3. **Partitioning**: 2 partitions alignées sur architecture workers
4. **Memory management**: Driver 3GB + Executor 6GB partagé

### Optimisations PostgreSQL

1. **Primary key composite**: Prévient les doublons naturellement
2. **Index GIST spatial**: Accélère les requêtes géographiques
3. **Batch size 10k**: Optimise les écritures JDBC
4. **Isolation READ_COMMITTED**: Évite les verrous prolongés

### Optimisations mémoire

1. **Container limits**: 4GB strict avec swap control
2. **Partition sizing**: Taille optimisée pour éviter OOM
3. **Temp table pattern**: Évite les buffers mémoire Spark excessifs
4. **Cleanup automatique**: Libération mémoire après traitement

## Limitations et évolutions

### Limitations actuelles

1. **Single-shot import**: Pas de mise à jour incrémentale
2. **Memory bounds**: Limité à 4GB pour très gros datasets
3. **Pas de versioning**: Pas d'historique des modifications
4. **Validation basique**: Contrôles limités sur cohérence métier

### Évolutions futures

1. **Delta processing**: Import incrémental des nouvelles données
2. **Data quality**: Validation métier avancée (prix aberrants, etc.)
3. **Partitioning avancé**: Partition par région/département
4. **Real-time updates**: Pipeline de mise à jour temps réel
5. **ML validation**: Détection automatique d'anomalies par ML

Le service properties-importer représente une pipeline robuste et performante pour l'importation de données immobilières massives, démontrant l'efficacité de l'architecture Spark + PostGIS pour le traitement de données géospatiales volumineuses.