# Hadoop Ecosystem - Stockage distribué HDFS

## Vue d'ensemble

L'écosystème Hadoop de Homepedia fournit une infrastructure de stockage distribué (HDFS) pour gérer les fichiers géospatiauxaux volumineux. Il est composé de trois containers Docker orchestrant le stockage et le chargement des données GeoJSON utilisées par les services de traitement Spark.

## Architecture HDFS

### Composants principaux

1. **NameNode** - Nœud maître gérant les métadonnées
2. **DataNode** - Nœud de stockage des données  
3. **HDFS-Loader** - Service de chargement initial des données

### Infrastructure technique

```
HDFS Cluster (hadoop-cluster)
├── NameNode (namenode)          # Gestionnaire métadonnées
│   ├── Port 9870                # Interface web
│   ├── Port 9000                # Communication HDFS
│   └── Volume: hadoop_namenode   # Persistance métadonnées
├── DataNode (datanode)          # Stockage physique
│   └── Volume: hadoop_datanode   # Persistance données
└── HDFS-Loader (hdfs-loader)    # Chargement initial
    └── Script: hdfs-loader.sh    # Orchestration chargement
```

## Container NameNode

### Configuration Docker

```yaml
namenode:
  image: bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8
  platform: linux/amd64
  container_name: namenode
  restart: always
  ports:
    - "9870:9870"  # Interface web Hadoop
    - "9000:9000"  # Communication HDFS
  environment:
    - CLUSTER_NAME=hadoop-cluster
    - CORE_CONF_fs_defaultFS=hdfs://namenode:9000
```

### Fonctionnalités

**Rôle principal**:
- Gestion des métadonnées du système de fichiers distribué
- Mapping des blocs de données vers les DataNodes
- Point d'entrée pour toutes les opérations HDFS

**Interface web** (http://localhost:9870):
- Vue d'ensemble du cluster HDFS
- Statistiques d'utilisation du stockage
- État des DataNodes connectés
- Navigation dans l'arborescence HDFS

**Stockage persistant**:
- Volume `hadoop_namenode` pour la persistance des métadonnées
- Répertoire `/hadoop/dfs/name` dans le container

## Container DataNode

### Configuration Docker

```yaml
datanode:
  image: bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8
  platform: linux/amd64
  container_name: datanode
  restart: always
  environment:
    - CORE_CONF_fs_defaultFS=hdfs://namenode:9000
  depends_on:
    - namenode
```

### Fonctionnalités

**Rôle principal**:
- Stockage physique des blocs de données
- Communication avec le NameNode pour les opérations
- Réplication et intégrité des données

**Configuration**:
- Connexion automatique au NameNode via `hdfs://namenode:9000`
- Volume persistant `hadoop_datanode` pour le stockage
- Répertoire `/hadoop/dfs/data` pour les blocs

## Container HDFS-Loader

### Configuration Docker

```yaml
hdfs-loader:
  image: bde2020/hadoop-base:2.0.0-hadoop3.2.1-java8
  platform: linux/amd64
  container_name: hdfs-loader
  depends_on: [namenode, datanode]
  environment:
    - CORE_CONF_fs_defaultFS=hdfs://namenode:9000
  volumes:
    - ./geo_importer/geojson_files:/geojson_files
    - ./geo_importer/hdfs-loader.sh:/hdfs-loader.sh
  command: bash /hdfs-loader.sh
  restart: on-failure
```

### Script de chargement (hdfs-loader.sh)

Le script `hdfs-loader.sh` orchestré le processus de chargement initial des données:

#### Phase 1: Attente du cluster HDFS

```bash
echo "Attente de la disponibilité du NameNode..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if hdfs dfs -ls hdfs://namenode:9000/ >/dev/null 2>&1; then
        echo "NameNode disponible!"
        break
    fi
    attempt=$((attempt + 1))
    sleep 2
done
```

#### Phase 2: Préparation de l'arborescence

```bash
echo "Création du répertoire de données dans HDFS..."
hdfs dfs -mkdir -p hdfs://namenode:9000/data
```

#### Phase 3: Chargement des fichiers GeoJSON

```bash
echo "Chargement des fichiers GeoJSON dans HDFS..."
for file in communes-1000m.geojson departements-1000m.geojson regions-1000m.geojson; do
    if [ -f "/geojson_files/$file" ]; then
        echo "Chargement de $file..."
        hdfs dfs -copyFromLocal -f /geojson_files/$file hdfs://namenode:9000/data/
        echo "$file chargé avec succès"
    else
        echo "ATTENTION: $file non trouvé!"
    fi
done
```

## Données stockées

### Fichiers GeoJSON chargés

1. **communes-1000m.geojson** (10.0 MB)
   - Géométries simplifiées des communes françaises
   - Résolution 1000m pour optimiser les performances
   - Utilisé pour l'affichage cartographique détaillé

2. **departements-1000m.geojson** (338 KB)
   - Géométries des départements français
   - Niveau intermédiaire de granularité
   - Affichage zoom moyen

3. **regions-1000m.geojson** (148 KB)
   - Géométries des régions françaises
   - Vue d'ensemble nationale
   - Affichage zoom faible

### Arborescence HDFS

```
hdfs://namenode:9000/
└── data/
    ├── communes-1000m.geojson
    ├── departements-1000m.geojson
    └── regions-1000m.geojson
```

## Intégration avec Spark

### Configuration d'accès

Les services Spark accèdent aux données HDFS via des variables d'environnement:

```bash
# Geo Data Importer
HDFS_CITIES_PATH=hdfs://namenode:9000/data/communes-1000m.geojson
HDFS_DEPARTMENTS_PATH=hdfs://namenode:9000/data/departements-1000m.geojson
HDFS_REGIONS_PATH=hdfs://namenode:9000/data/regions-1000m.geojson
```

### Lecture depuis Spark

```python
# geo_importer/geojson_processing.py
from pyspark.sql import SparkSession

# Lecture directe depuis HDFS
df_raw_cities = spark.read.json(os.getenv('HDFS_CITIES_PATH'))
df_raw_depts = spark.read.json(os.getenv('HDFS_DEPARTMENTS_PATH'))
df_raw_regions = spark.read.json(os.getenv('HDFS_REGIONS_PATH'))
```

## Performance et monitoring

### Métriques du cluster

**Utilisation actuelle**:
- Système de fichiers: hdfs://namenode:9000
- Taille totale: 62.6 GB
- Espace utilisé: 10.6 MB (fichiers GeoJSON)
- Espace disponible: 4.4 GB
- Utilisation: 0%

**Interface de monitoring**:
- URL: http://localhost:9870
- Métriques temps réel du cluster
- État des DataNodes
- Statistiques de réplication

### Commandes de diagnostic

```bash
# Vérification de l'état du cluster
docker exec namenode hdfs dfsadmin -report

# Liste des fichiers dans HDFS
docker exec namenode hdfs dfs -ls /data

# Informations détaillées d'un fichier
docker exec namenode hdfs dfs -stat "%n %o %r %u %g %s %b %c %y" /data/communes-1000m.geojson

# Vérification de l'intégrité
docker exec namenode hdfs fsck /data -files -blocks
```

## Réseau et communication

### Configuration réseau

- **Réseau Docker**: `t-dat-902-network` (bridge)
- **Résolution DNS**: Communication par noms de containers
- **Port mapping**: 
  - 9870:9870 (Interface web)
  - 9000:9000 (Communication HDFS)

### Flux de communication

```
Client/Spark → NameNode (métadonnées) → DataNode (données)
     ↓
hdfs://namenode:9000/data/file.geojson
```

## Haute disponibilité et récupération

### Stratégies de résilience

1. **Restart policy**: `restart: always` pour NameNode/DataNode
2. **Volumes persistants**: Conservation des données entre redémarrages
3. **Healthchecks**: Monitoring automatique de l'état des services
4. **Dépendances**: Ordre de démarrage respecté

### Procédures de récupération

```bash
# Redémarrage du cluster complet
docker compose restart namenode datanode hdfs-loader

# Rechargement des données uniquement
docker compose restart hdfs-loader

# Vérification de l'intégrité après récupération
docker exec namenode hdfs fsck /data
```

## Dépendances dans l'architecture

### Chaîne de dépendances

```
1. namenode         # Démarre en premier
2. datanode         # Dépend du namenode
3. hdfs-loader      # Dépend de namenode + datanode
4. spark-master     # Indépendant mais utilise HDFS
5. geo-data-importer # Dépend de hdfs-loader + spark
```

### Impact sur le pipeline

- **Prérequis**: HDFS doit être opérationnel avant Spark
- **Données sources**: Fichiers GeoJSON accessibles depuis HDFS
- **Pipeline complet**: Hadoop → Spark → PostgreSQL

## Limitations et évolutions

### Limitations actuelles

1. **Cluster single-node**: Pas de réplication pour la haute disponibilité
2. **Pas de sécurité**: Accès HDFS non sécurisé
3. **Configuration statique**: Paramètres hardcodés
4. **Monitoring basique**: Pas d'alertes automatiques

### Évolutions futures

1. **Multi-DataNode**: Ajout de DataNodes pour la réplication
2. **Sécurité Kerberos**: Authentification et autorisation
3. **Configuration externalisée**: Variables d'environnement complètes
4. **Monitoring avancé**: Intégration avec Prometheus/Grafana
5. **Backup automatique**: Sauvegarde régulière des données critiques

L'écosystème Hadoop de Homepedia fournit une fondation robuste pour le stockage et l'accès distribué aux données géospatiales, intégré de manière transparente avec l'infrastructure Spark pour le traitement des données volumineuses.