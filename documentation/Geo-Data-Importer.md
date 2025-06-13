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

Configuration Spark optimisée avec:
- Allocation mémoire driver (2G) et executor (1G)
- Support adaptatif des requêtes SQL
- Chargement automatique du driver JDBC PostgreSQL

### Lecture des données HDFS

- Lecture distribuée des fichiers GeoJSON depuis Hadoop
- Extraction des features GeoJSON via explosion des collections
- Création de DataFrames Spark pour chaque niveau administratif

### Transformations géospatiales

#### Extraction des propriétés

- Extraction des métadonnées depuis les properties GeoJSON
- Mapping des codes INSEE (commune, département, région)
- Séparation des géométries pour traitement spécialisé

#### Conversion géométrique

Processus de transformation des géométries GeoJSON vers format WKT:
- Conversion des structures Spark Row vers dictionnaires GeoJSON
- Nettoyage automatique des coordonnées malformées (chaînes → nombres)
- Validation géométrique avec correction automatique (buffer(0))
- Normalisation en MultiPolygon pour cohérence PostGIS
- Gestion d'erreurs avec fallback et logging

#### Nettoyage des coordonnées

- Parsing récursif des coordonnées malformées
- Conversion des chaînes "[-61.549,16.253]" vers listes numériques
- Support des structures imbriquées (MultiPolygon complexes)
- Validation des formats et correction automatique

## Intégration PostgreSQL/PostGIS

### Schéma de base de données

Structure hiérarchique à trois niveaux:
- **Régions** (18): Identifiant, nom, géométrie MULTIPOLYGON
- **Départements** (101): Rattachement région, géométrie, clé étrangère
- **Communes** (34,945): Rattachement département/région, géométrie

Toutes les géométries utilisent le système de coordonnées WGS84 (SRID 4326).

### Index spatiaux

- Index GIST sur toutes les colonnes géométriques
- Optimisation des requêtes spatiales (intersections, containement)
- Performance améliorée pour les requêtes géospatiales complexes

### Insertion distribuée

Stratégie d'insertion optimisée par partition Spark:
- Une connexion PostgreSQL par partition (réduction overhead)
- Insertion avec UPSERT (ON CONFLICT DO UPDATE) pour idempotence
- Validation géométrique avant insertion (filtrage nulls)
- Gestion transactionnelle avec rollback en cas d'erreur
- Conversion automatique WKT vers géométrie PostGIS (ST_GeomFromText)
- Exécution parallèle sur toutes les partitions Spark

## Processus de chargement HDFS

### Script hdfs-loader.sh

Script de chargement HDFS avec mécanisme de résilience:
- Attente active du NameNode avec retry automatique (60 tentatives)
- Création de l'arborescence HDFS (/data/)
- Chargement séquentiel des 3 fichiers GeoJSON
- Validation de présence avant chargement
- Logs détaillés pour monitoring et debugging
- Gestion d'erreurs avec exit codes appropriés

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

Outil de validation visuelle des géométries importées:
- Génération de carte interactive Folium centrée sur la France
- Couches séparées par niveau administratif (régions, départements, communes)
- Styles différenciés pour identification visuelle
- Conversion WKT vers GeoJSON pour affichage
- Export HTML pour validation manuelle
- Détection visuelle des erreurs géométriques

### Contrôles automatiques

1. **Validation géométrique**: `shapely_geom.is_valid`
2. **Correction automatique**: `buffer(0)` pour géométries invalides
3. **Vérification relations**: Clés étrangères respectées
4. **Test d'intégrité**: Requêtes spatiales PostGIS

## Performance et optimisations

### Configuration Spark

Optimisations de performance:
- Requêtes SQL adaptatives activées
- Coalescing automatique des partitions
- Sérialisation Kryo pour meilleure performance
- Allocation mémoire optimisée (2G driver, 1G executor)

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