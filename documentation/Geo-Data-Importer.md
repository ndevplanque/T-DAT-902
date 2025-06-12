# Geo Data Importer - Service d'importation géospatiale

## Vue d'ensemble

Le service **geo-data-importer** est un composant central de l'infrastructure Homepedia qui orchestré l'importation et le traitement des données géospatiales françaises. Il utilise Apache Spark et Hadoop HDFS pour traiter de gros volumes de données GeoJSON et les insérer dans une base PostgreSQL avec PostGIS.

## Architecture du service

### Responsabilités principales

1. **Chargement HDFS**: Transfert des fichiers GeoJSON vers le stockage distribué
2. **Traitement Spark**: Transformation et validation des géométries à l'échelle
3. **Import PostgreSQL**: Insertion dans la base géospatiale avec optimisations
4. **Validation**: Contrôle de qualité et correction automatique des données

### Structure des composants

```
geo_importer/
├── Container Principal
│   ├── geojson_processing.py     # Script Spark principal
│   ├── entrypoint.sh            # Point d'entrée avec vérifications
│   └── requirements.txt         # Dépendances Python
├── Container HDFS-Loader
│   └── hdfs-loader.sh           # Script de chargement HDFS
├── Workers Spark Personnalisés
│   ├── Dockerfile.spark-worker   # Worker géospatial
│   └── Dockerfile.spark-worker-2 # Worker haute performance
├── Données Sources
│   └── geojson_files/           # Fichiers géospatiaux
└── Infrastructure
    └── jars/postgresql-42.7.4.jar # Driver JDBC
```

## Configuration Docker

### Service principal

```yaml
geo-data-importer:
  build:
    context: ./geo_importer
    dockerfile: Dockerfile
  container_name: geo-data-importer
  restart: "no"
  depends_on:
    - postgres
    - namenode
    - datanode
    - spark-master
    - spark-worker
    - hdfs-loader
```

### Variables d'environnement

```bash
# Configuration PostgreSQL
POSTGRES_DB=gis_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Configuration Spark
SPARK_APP_NAME=GeoJSON_Import
SPARK_MASTER=spark://spark-master:7077
SPARK_JARS=/app/jars/postgresql-42.7.4.jar

# Chemins HDFS des données
HDFS_CITIES_PATH=hdfs://namenode:9000/data/communes-1000m.geojson
HDFS_DEPARTMENTS_PATH=hdfs://namenode:9000/data/departements-1000m.geojson
HDFS_REGIONS_PATH=hdfs://namenode:9000/data/regions-1000m.geojson

# Configuration runtime
PYSPARK_PYTHON=/usr/bin/python3.9
PYSPARK_DRIVER_PYTHON=/usr/bin/python3.9
```

## Données géospatiales traitées

### Sources de données

1. **communes-1000m.geojson** (10.0 MB)
   - 34,945 communes françaises
   - Géométries simplifiées (résolution 1000m)
   - Métadonnées: code commune, nom, rattachements

2. **departements-1000m.geojson** (338 KB)
   - 101 départements français
   - Géométries départementales complètes
   - Relations hiérarchiques avec régions

3. **regions-1000m.geojson** (148 KB)  
   - 18 régions françaises
   - Contours administratifs actuels
   - Niveau administratif le plus élevé

### Format et structure

```json
// Structure type d'un feature GeoJSON
{
  "type": "Feature",
  "properties": {
    "code": "01001",                    // Code INSEE
    "nom": "L'Abergement-Clémenciat",  // Nom administratif
    "code_dept": "01",                 // Code département
    "code_reg": "84"                   // Code région
  },
  "geometry": {
    "type": "MultiPolygon",
    "coordinates": [[[...coordinates...]]]
  }
}
```

## Pipeline de traitement Spark

### Initialisation de session

```python
# Configuration Spark optimisée
spark = SparkSession.builder \
    .appName("GeoJSON_Import") \
    .master("spark://spark-master:7077") \
    .config("spark.jars", "/app/jars/postgresql-42.7.4.jar") \
    .config("spark.driver.memory", "2g") \
    .config("spark.executor.memory", "1g") \
    .config("spark.sql.adaptive.enabled", "true") \
    .getOrCreate()
```

### Lecture des données HDFS

```python
# Lecture distribuée depuis Hadoop
df_raw_cities = spark.read.json(HDFS_CITIES_PATH)
df_raw_depts = spark.read.json(HDFS_DEPARTMENTS_PATH)
df_raw_regions = spark.read.json(HDFS_REGIONS_PATH)

# Extraction des features GeoJSON
df_cities = df_raw_cities.select(explode(col("features")).alias("feature"))
df_departments = df_raw_depts.select(explode(col("features")).alias("feature"))
df_regions = df_raw_regions.select(explode(col("features")).alias("feature"))
```

### Transformations géospatiales

#### Extraction des propriétés

```python
# Extraction des métadonnées
df_cities = df_cities.select(
    col("feature.properties.code").alias("city_id"),
    col("feature.properties.nom").alias("name"),
    col("feature.properties.code_dept").alias("department_id"),
    col("feature.properties.code_reg").alias("region_id"),
    col("feature.geometry").alias("geometry")
)
```

#### Conversion géométrique

```python
def geojson_to_wkt(geometry_row):
    """
    Convertit une géométrie GeoJSON en format WKT (Well-Known Text)
    avec validation et correction automatique
    """
    try:
        # Conversion Row Spark → dict GeoJSON
        geometry_dict = geometry_row.asDict()
        
        # Nettoyage des coordonnées malformées
        geometry_dict = clean_coords(geometry_dict)
        
        # Création objet Shapely
        shapely_geom = shape(geometry_dict)
        
        # Validation et correction si nécessaire
        if not shapely_geom.is_valid:
            shapely_geom = shapely_geom.buffer(0)
        
        # Normalisation en MultiPolygon
        if shapely_geom.geom_type == 'Polygon':
            shapely_geom = MultiPolygon([shapely_geom])
        
        return shapely_geom.wkt
        
    except Exception as e:
        print(f"Erreur conversion géométrie: {e}")
        return None
```

#### Nettoyage des coordonnées

```python
def clean_coords(coords):
    """
    Nettoie récursivement les coordonnées malformées
    Exemple: "[-61.549,16.253]" → [-61.549, 16.253]
    """
    if isinstance(coords, list):
        return [clean_coords(item) for item in coords]
    elif isinstance(coords, str):
        return parse_coordinate_string(coords)
    else:
        return coords

def parse_coordinate_string(s):
    """Parse les chaînes de coordonnées au format [-61.549,16.253]"""
    s = s.strip()
    if s.startswith('[') and s.endswith(']'):
        content = s[1:-1]  # Supprime les crochets
        parts = content.split(',')
        return [float(part.strip()) for part in parts]
    return s
```

## Intégration PostgreSQL/PostGIS

### Schéma de base de données

```sql
-- Table des régions (18 enregistrements)
CREATE TABLE regions (
    region_id VARCHAR(10) PRIMARY KEY,
    name TEXT NOT NULL,
    geom GEOMETRY(MULTIPOLYGON, 4326)
);

-- Table des départements (101 enregistrements)
CREATE TABLE departments (
    department_id VARCHAR(10) PRIMARY KEY,
    name TEXT NOT NULL,
    region_id VARCHAR(10) NOT NULL,
    geom GEOMETRY(MULTIPOLYGON, 4326),
    FOREIGN KEY (region_id) REFERENCES regions(region_id)
);

-- Table des communes (34,945 enregistrements)
CREATE TABLE cities (
    city_id VARCHAR(10) PRIMARY KEY,
    name TEXT NOT NULL,
    department_id VARCHAR(10) NOT NULL,
    region_id VARCHAR(10) NOT NULL,
    geom GEOMETRY(MULTIPOLYGON, 4326),
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (region_id) REFERENCES regions(region_id)
);
```

### Index spatiaux

```sql
-- Index GIST pour optimiser les requêtes spatiales
CREATE INDEX idx_regions_geom ON regions USING GIST (geom);
CREATE INDEX idx_departments_geom ON departments USING GIST (geom);
CREATE INDEX idx_cities_geom ON cities USING GIST (geom);
```

### Insertion distribuée

```python
def insert_partition_cities(rows):
    """
    Fonction exécutée sur chaque partition Spark
    pour minimiser les connexions PostgreSQL
    """
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        database=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    
    try:
        cur = conn.cursor()
        sql = """
            INSERT INTO cities (city_id, name, department_id, region_id, geom)
            VALUES (%s, %s, %s, %s, ST_GeomFromText(%s, 4326))
            ON CONFLICT (city_id) DO UPDATE SET
                name = EXCLUDED.name,
                geom = EXCLUDED.geom;
        """
        
        for row in rows:
            if row.geom:  # Seulement si géométrie valide
                cur.execute(sql, (
                    row.city_id,
                    row.name,
                    row.department_id,
                    row.region_id,
                    row.geom
                ))
        
        conn.commit()
        
    except Exception as e:
        print(f"Erreur insertion: {e}")
        conn.rollback()
    finally:
        conn.close()

# Exécution distribuée par partition
df_cities_with_geom.foreachPartition(insert_partition_cities)
```

## Processus de chargement HDFS

### Script hdfs-loader.sh

```bash
#!/bin/bash
echo "Attente de la disponibilité du NameNode..."

# Attente avec retry automatique
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if hdfs dfs -ls hdfs://namenode:9000/ >/dev/null 2>&1; then
        echo "NameNode disponible!"
        break
    fi
    attempt=$((attempt + 1))
    echo "Tentative $attempt/$max_attempts..."
    sleep 2
done

# Préparation de l'arborescence HDFS
echo "Création du répertoire de données dans HDFS..."
hdfs dfs -mkdir -p hdfs://namenode:9000/data

# Chargement des fichiers GeoJSON
for file in communes-1000m.geojson departements-1000m.geojson regions-1000m.geojson; do
    if [ -f "/geojson_files/$file" ]; then
        echo "Chargement de $file..."
        hdfs dfs -copyFromLocal -f /geojson_files/$file hdfs://namenode:9000/data/
        echo "$file chargé avec succès"
    else
        echo "ATTENTION: $file non trouvé!"
        exit 1
    fi
done

echo "Chargement HDFS terminé avec succès!"
```

## Dépendances et technologies

### Dépendances Python

```txt
pyspark==3.4.1          # Framework Spark
numpy==1.24.3           # Calculs numériques
shapely                 # Manipulation géométries
psycopg2-binary        # Driver PostgreSQL/PostGIS
python-dotenv==1.0.0   # Variables d'environnement
```

### JAR et drivers

**PostgreSQL JDBC Driver**:
- Fichier: `postgresql-42.7.4.jar` (1.1 MB)
- Fonction: Connectivité JDBC entre Spark et PostgreSQL
- Configuration: Automatiquement ajouté au classpath Spark

## Validation et contrôle qualité

### Script de test (test_polygons.py)

```python
import folium
import psycopg2
from shapely.wkt import loads

def create_validation_map():
    """Génère une carte interactive pour validation visuelle"""
    m = folium.Map(location=[46.0, 2.0], zoom_start=6)
    
    # Couches séparées par niveau administratif
    cities_layer = folium.FeatureGroup(name='Communes')
    departments_layer = folium.FeatureGroup(name='Départements')
    regions_layer = folium.FeatureGroup(name='Régions')
    
    # Ajout des géométries avec styles différents
    for region in get_regions():
        geom = loads(region['geom'])
        folium.GeoJson(
            geom.__geo_interface__,
            style_function=lambda x: {'fillColor': 'red', 'weight': 2}
        ).add_to(regions_layer)
    
    # Export en HTML pour validation
    m.save('test_map.html')
```

### Contrôles automatiques

1. **Validation géométrique**: `shapely_geom.is_valid`
2. **Correction automatique**: `buffer(0)` pour géométries invalides
3. **Vérification relations**: Clés étrangères respectées
4. **Test d'intégrité**: Requêtes spatiales PostGIS

## Performance et optimisations

### Configuration Spark

```python
# Optimisations mémoire et calcul
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
```

### Optimisations PostgreSQL

1. **Index spatiaux GIST**: Sur toutes les colonnes geometry
2. **ON CONFLICT DO UPDATE**: Idempotence des insertions
3. **Transactions par partition**: Minimise les connexions
4. **Batch processing**: Insert groupés par partition

### Métriques de performance

- **Données traitées**: 34,945 communes + 101 départements + 18 régions
- **Taille totale**: ~10.5 MB de données géospatiales
- **Temps d'exécution**: ~2-5 minutes (selon ressources)
- **Parallélisme**: 4 partitions Spark par défaut

## Limitations et évolutions

### Limitations actuelles

1. **Géométries simplifiées**: Résolution 1000m pour performance
2. **Pas de versioning**: Pas de gestion historique des modifications
3. **Single-shot**: Pas de mise à jour incrémentale
4. **Validation limitée**: Contrôles basiques de géométrie

### Évolutions futures

1. **Multi-résolution**: Support de différentes précisions géométriques
2. **Delta updates**: Mise à jour incrémentale des modifications
3. **Monitoring avancé**: Métriques détaillées de performance
4. **Validation étendue**: Contrôles topologiques approfondis
5. **Backup automatique**: Sauvegarde avant chaque import

Le service geo-data-importer constitue une pipeline robuste et scalable pour l'importation de données géospatiales françaises, avec une architecture distribuée moderne intégrant Spark, HDFS et PostGIS de manière optimale.