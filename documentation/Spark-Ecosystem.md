# Spark Ecosystem - Cluster de traitement distribué

## Vue d'ensemble

L'écosystème Apache Spark de Homepedia constitue le moteur de traitement distribué pour les données géospatiales, immobilières et textuelles. Il est composé d'un cluster master-workers avec 2 nœuds de calcul optimisés pour différents types de workloads, intégré avec HDFS, PostgreSQL et MongoDB.

## Architecture du cluster Spark

### Configuration Master-Workers

```
Spark Cluster (spark://spark-master:7077)
├── Spark Master (spark-master)      # Orchestrateur central
│   ├── Port 8080                    # Interface web
│   ├── Port 7077                    # Communication cluster
│   └── Ressources totales: 6 cores, 12 GiB
├── Spark Worker 1 (spark-worker)    # Worker équilibré
│   ├── 2 cores, 4 GiB               # Configuration standard
│   └── Spécialisé: Geo-processing   
└── Spark Worker 2 (spark-worker-2)  # Worker haute performance
    ├── 4 cores, 8 GiB               # Configuration renforcée
    └── Spécialisé: Property data
```

## Container Spark Master

### Configuration Docker

```yaml
spark-master:
  image: bitnami/spark:3.4.1
  platform: linux/amd64
  container_name: spark-master
  restart: always
  environment:
    - SPARK_MODE=master
    - SPARK_MASTER_HOST=spark-master
  ports:
    - "8080:8080"  # Interface web Spark UI
    - "7077:7077"  # Communication master-workers
```

### Fonctionnalités

**Rôle principal**:
- Orchestration des jobs Spark distribués
- Allocation des ressources aux applications
- Monitoring et gestion du cluster
- Interface de soumission des jobs

**Interface web** (http://localhost:8080):
- État en temps réel du cluster
- Applications en cours et historique
- Métriques de performance workers
- Logs d'exécution des jobs

**Ressources gérées**:
- 2 workers connectés
- 6 cores total disponibles
- 12.0 GiB RAM total
- État: ALIVE et opérationnel

### JVM et optimisations

```bash
JAVA_OPTS=-Dio.netty.tryReflectionSetAccessible=true 
--add-opens=java.base/java.nio=ALL-UNNAMED 
--add-opens=java.base/sun.nio.ch=ALL-UNNAMED 
--add-opens=java.base/java.util=ALL-UNNAMED
```

**Optimisations appliquées**:
- Compatible Java 17+ avec accès réflexif
- Optimisation Netty pour communications réseau
- Gestion mémoire optimisée pour big data

## Container Spark Worker 1

### Configuration Docker

```yaml
spark-worker:
  build:
    context: ./geo_importer
    dockerfile: Dockerfile.spark-worker
  platform: linux/amd64
  container_name: spark-worker
  restart: always
```

### Dockerfile personnalisé

```dockerfile
FROM bitnami/spark:3.4.1

# Installation dépendances Python géospatiales
USER root
RUN pip install shapely psycopg2-binary

# Configuration utilisateur
USER 1001
```

### Configuration des ressources

```bash
# Allocation ressources
SPARK_WORKER_MEMORY=4G
SPARK_WORKER_CORES=2
SPARK_DAEMON_MEMORY=1g

# Configuration Python
PYSPARK_PYTHON=/opt/bitnami/python/bin/python3
SPARK_MASTER_URL=spark://spark-master:7077
```

### Spécialisation: Geo-processing

**Dépendances installées**:
- **Shapely**: Manipulation géométries complexes
- **psycopg2-binary**: Connecteur PostgreSQL/PostGIS
- **Support GeoJSON**: Traitement fichiers géospatiaux

**Volumes montés**:
- JARs PostgreSQL JDBC: `/opt/bitnami/spark/custom-jars`
- Données immobilières: `/properties/CSV_DVF`

**Performance actuelle**:
- CPU: 0.13% (faible charge)
- Mémoire: 320.4MiB / 3.828GiB (8.17%)
- État: Registered et connecté

## Container Spark Worker 2

### Configuration Docker

```yaml
spark-worker-2:
  build:
    context: ./geo_importer
    dockerfile: Dockerfile.spark-worker-2
  platform: linux/amd64
  container_name: spark-worker-2
  restart: always
```

### Configuration renforcée

```bash
# Ressources doublées pour gros volumes
SPARK_WORKER_MEMORY=8G
SPARK_WORKER_CORES=4
SPARK_DAEMON_MEMORY=1g
```

### Spécialisation: Property data processing

**Optimisations**:
- Mémoire doublée pour traitement CSV volumineux
- CPU renforcé pour calculs intensifs
- Pas d'accès aux JARs geo (optimisation)

**Performance actuelle**:
- CPU: 0.17% (légèrement plus élevé)
- Mémoire: 339.5MiB / 3.828GiB (8.66%)
- État: Registered et opérationnel

## Intégration avec HDFS

### Configuration d'accès

```bash
# Variables d'environnement pour accès HDFS
HDFS_CITIES_PATH=hdfs://namenode:9000/data/communes-1000m.geojson
HDFS_DEPARTMENTS_PATH=hdfs://namenode:9000/data/departements-1000m.geojson
HDFS_REGIONS_PATH=hdfs://namenode:9000/data/regions-1000m.geojson
```

### Données accessibles

**Fichiers GeoJSON dans HDFS**:
- `communes-1000m.geojson` (10.05 MB) - 34,455 communes
- `departements-1000m.geojson` (338 KB) - Départements français
- `regions-1000m.geojson` (148 KB) - Régions françaises

**Métriques HDFS**:
- Espace total: 58.37 GB
- Espace utilisé: 10.18 MB (0.24%)
- Espace disponible: 4.16 GB
- Factor de réplication: 3

## Pipelines de traitement Spark

### 1. Geo Data Processing Pipeline

**Service**: `geo-data-importer`
**Script**: `geojson_processing.py`

```python
# Configuration Spark
spark = SparkSession.builder \
    .appName("GeoJSON_Import") \
    .master("spark://spark-master:7077") \
    .config("spark.jars", "/app/jars/postgresql-42.7.4.jar") \
    .getOrCreate()
```

**Processus de traitement**:
1. Lecture des GeoJSON depuis HDFS
2. Parsing et validation des géométries
3. Transformation avec Shapely
4. Insertion en PostgreSQL via JDBC

**Optimisations**:
- Lecture distribuée depuis HDFS
- Traitement parallèle des géométries
- Batch insertion en PostgreSQL

### 2. Property Data Processing Pipeline

**Service**: `properties-importer`
**Script**: `csv_treatment.py`

```python
# Configuration optimisée pour gros volumes
CHUNK_SIZE=10000
CSV_DVF_PATH=/properties/CSV_DVF
```

**Processus de traitement**:
1. Lecture des fichiers CSV DVF par chunks
2. Nettoyage et validation des données
3. Géolocalisation et jointures spatiales
4. Agrégation et insertion PostgreSQL

**Gestion mémoire**:
- Traitement par chunks de 10k lignes
- Évite les Out-Of-Memory errors
- Parallélisation optimisée

### 3. Text Processing Pipeline

**Service**: `avis-processor-submitter`
**Script**: `word_processor.py`

**Métriques de traitement**:
- 34,455 villes analysées (100% completion)
- 54,656 avis traités
- 368,672 mots extraits
- Moyenne: 35.61 mots par ville

**Analyse de sentiment**:
- 36.15% sentiments positifs
- 51.87% sentiments neutres
- 11.99% sentiments négatifs

**Technologies utilisées**:
- SpaCy pour NLP
- MongoDB pour stockage résultats
- Parallélisation par ville

## Gestion des dépendances

### JARs et drivers

**PostgreSQL JDBC** (`postgresql-42.7.4.jar`):
- Montage: `/opt/bitnami/spark/custom-jars/`
- CLASSPATH: Automatiquement inclus
- Utilisé pour: Geo-data et Property-data

**Configuration JDBC**:
```python
# Propriétés de connexion PostgreSQL
jdbc_url = "jdbc:postgresql://postgres:5432/gis_db"
properties = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver"
}
```

### Dépendances Python

**Worker géospatial**:
- `shapely`: Manipulation géométries
- `psycopg2-binary`: Driver PostgreSQL natif

**Worker text processing**:
- `spacy`: Traitement langage naturel
- `pymongo`: Driver MongoDB
- `wordcloud`: Génération nuages de mots

## Configuration réseau et communication

### Réseau Docker

- **Réseau**: `t-dat-902-network` (bridge)
- **Communication interne**: Par noms de containers
- **Master endpoint**: `spark://spark-master:7077`

### Ports et services

```bash
# Spark Master
8080:8080  # Interface web Spark UI
7077:7077  # Communication cluster

# Workers
# Ports dynamiques assignés par Spark Master
```

### Flux de communication

```
Client → Spark Master → Workers
    ↓
Application Job → Task Distribution → Results Aggregation
```

## Monitoring et métriques

### Interface Spark UI

**URL**: http://localhost:8080

**Fonctionnalités**:
- État temps réel du cluster
- Historique des applications
- Métriques par worker
- Logs d'exécution détaillés
- Graphiques de performance

### Métriques de performance

**Cluster global**:
- 2 workers actifs
- 6 cores disponibles
- 12.0 GiB RAM total
- 0 applications en cours

**Worker 1** (geo-processing):
- Utilisation CPU: 0.13%
- Mémoire: 320.4MiB / 3.828GiB
- Statut: Running

**Worker 2** (property-processing):
- Utilisation CPU: 0.17%
- Mémoire: 339.5MiB / 3.828GiB
- Statut: Running

### Commandes de diagnostic

```bash
# État du cluster Spark
docker exec spark-master spark-shell --version

# Logs du master
docker logs spark-master

# Logs des workers
docker logs spark-worker
docker logs spark-worker-2

# Applications Spark actives
curl http://localhost:8080/api/v1/applications
```

## Intégrations bases de données

### PostgreSQL (PostGIS)

**Configuration**:
- Host: postgres:5432
- Database: gis_db
- Driver: JDBC PostgreSQL

**Tables gérées**:
- `regions`: Géométries régions
- `departments`: Géométries départements
- `cities`: Géométries communes
- `properties`: Données immobilières

### MongoDB

**Configuration**:
- URI: mongodb://root:rootpassword@mongodb:27017/
- Database: villes_france

**Collections gérées**:
- `villes`: Informations et avis villes
- `avis`: Avis individuels détaillés
- `mots_villes`: Fréquences mots et sentiments

## Performance et optimisations

### Optimisations mémoire

1. **Partitioning intelligent**: Données partitionnées selon la taille
2. **Cache stratégique**: DataFrames fréquents mis en cache
3. **Garbage collection**: Configuration JVM optimisée
4. **Serialization**: Kryo serializer pour performance

### Optimisations calcul

1. **Broadcast variables**: Variables partagées optimisées
2. **Accumulators**: Compteurs distribués
3. **Lazy evaluation**: Évaluation différée des transformations
4. **Pipeline fusion**: Optimisation automatique des stages

## Limitations et évolutions

### Limitations actuelles

1. **Cluster fixe**: Pas d'auto-scaling dynamique
2. **Single datanode**: Point de défaillance HDFS
3. **Memory bounds**: Limites 4G/8G pour très gros datasets
4. **No GPU support**: Pas d'accélération GPU pour ML

### Évolutions futures

1. **Dynamic allocation**: Scaling automatique des ressources
2. **Multi-datanode**: Haute disponibilité HDFS
3. **GPU workers**: Support RAPIDS pour ML accéléré
4. **Streaming**: Traitement temps réel avec Spark Streaming
5. **ML Pipeline**: Intégration MLlib pour analytics avancés

L'écosystème Spark de Homepedia offre une infrastructure robuste et scalable pour le traitement distribué des données géospatiales, immobilières et textuelles, avec une architecture optimisée pour les workloads spécifiques du projet.