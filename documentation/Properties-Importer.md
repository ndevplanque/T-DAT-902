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

Configuration haute performance pour traitement des données DVF:
- Allocation mémoire: 3GB driver, 6GB executor
- Sérialisation Kryo pour performance binaire
- Garbage collector G1GC optimisé pour gros datasets
- 4 partitions de shuffle, parallélisme limité à 1
- Driver JDBC PostgreSQL chargé automatiquement

### Lecture et validation des données

Processus de chargement et nettoyage du fichier CSV DVF:
- Lecture avec gestion des caractères spéciaux et multilignes
- Inférence automatique du schéma
- Filtrage des données essentielles (coordonnées GPS, identifiants)
- Validation des plages de coordonnées GPS (-90/90 latitude, -180/180 longitude)
- Élimination des enregistrements avec valeurs nulles critiques

### Transformation et typage

Standardisation des types de données pour cohérence:
- Cast explicite des identifiants en String
- Conversion des dates au format DateType
- Conversion des valeurs numériques (prix, surfaces, coordonnées) en DoubleType
- Repartitioning en 2 partitions pour optimiser la distribution sur les workers
- Préparation des données pour l'insertion PostgreSQL

## Intégration PostgreSQL/PostGIS

### Schéma de table principal

Structure de table PostgreSQL optimisée pour les données DVF:
- **Clé primaire composite** (id_mutation, id_parcelle) pour prévenir les doublons
- **Colonnes de transaction**: date, valeur foncière, nature de mutation
- **Localisation administrative**: codes commune/postal, noms
- **Surfaces**: bâtie et terrain en double précision
- **Géométrie PostGIS**: Point en WGS84 (SRID 4326)

### Index pour performance

Optimisations de requête avec index stratégiques:
- **Index spatial GIST** sur géométrie pour requêtes géographiques
- **Index B-tree** sur code commune pour jointures fréquentes
- **Index sur date** pour filtres temporels
- **Index sur valeur foncière** pour requêtes de prix

### Import en deux phases

#### Phase 1: Table temporaire via Spark JDBC

Écriture optimisée des données brutes:
- Connexion JDBC avec batch de 10,000 enregistrements
- Isolation READ_COMMITTED pour éviter les verrous
- Mode overwrite pour table temporaire
- Transfert direct depuis Spark vers PostgreSQL

#### Phase 2: Transformation PostGIS + déduplication

Traitement final avec capacités géospatiales:
- Création de géométries Point à partir des coordonnées GPS
- Application du système de référence WGS84 (SRID 4326)
- Déduplication automatique via ON CONFLICT DO NOTHING
- Validation finale des coordonnées et insertion sélective

## Scripts et orchestration

### Script principal (csv_treatment.py)

Orchestration complète du pipeline de traitement:
1. **Initialisation** de la session Spark avec configuration optimisée
2. **Chargement** et validation du fichier CSV DVF
3. **Transformation** des types de données et nettoyage
4. **Écriture** dans table temporaire PostgreSQL
5. **Traitement PostGIS** final avec création des géométries
6. **Nettoyage** des ressources temporaires

### Script de soumission Spark

Lancement du job avec paramètres optimisés:
- Déploiement en mode client sur cluster Spark
- Allocation mémoire: 3GB driver, 6GB executor
- Utilisation de 6 cores au total
- Chargement automatique du JAR PostgreSQL

### Attente des dépendances

Script de synchronisation avec retry automatique:
- Vérification de disponibilité PostgreSQL via pg_isready
- Attente active avec intervalles de 2 secondes
- Garantit la disponibilité avant démarrage du traitement

## Géolocalisation et jointures spatiales

### Création des géométries

Transformation des coordonnées GPS en géométries PostGIS:
- **Fonction ST_MakePoint**: Création de points à partir de longitude/latitude
- **SRID 4326**: Application du système de référence WGS84 (standard GPS)
- **Validation automatique**: PostGIS contrôle la validité des géométries
- **Format optimal**: Type Point adapté aux coordonnées ponctuelles

### Jointures spatiales pour agrégation

Capacités de requêtes géospatiales avancées:
- **ST_Within**: Détection des propriétés contenues dans les communes
- **Agrégation spatiale**: Calcul de statistiques par zone géographique
- **Métriques combinées**: Nombre de transactions, prix moyens, superficies
- **Performance optimisée**: Utilisation des index GIST pour rapidité

## Tables d'agrégation créées

Le service properties-importer alimente les tables d'agrégation suivantes:

### 1. properties_cities_stats (30,860 villes)

Table d'agrégation des statistiques immobilières par ville:
- **Identifiants**: Code INSEE et nom de la commune
- **Compteurs**: Nombre total de transactions
- **Statistiques de prix**: Moyenne, médiane, minimum, maximum, prix au m²
- **Statistiques de surface**: Moyennes pour surfaces bâties et terrain
- **Temporalité**: Dates de première et dernière transaction
- **Densité**: Nombre de transactions par km² pour analyse spatiale

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