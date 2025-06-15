# Documentation du Projet Homepedia (T-DAT-902)

## Introduction

Homepedia est une plateforme complète d'analyse immobilière et urbaine qui combine données géographiques, transactions immobilières DVF et avis citoyens sur les villes françaises. Le projet utilise une architecture microservices moderne avec Big Data (Hadoop/Spark), bases de données multi-modales (PostgreSQL/MongoDB) et une interface web interactive.

## Architecture du Projet

Le projet s'organise autour de plusieurs composants interconnectés:

1. **Sources de données**:
   - Scraping d'avis sur les villes françaises depuis "bien-dans-ma-ville.fr"
   - Import de données géographiques GeoJSON (communes, départements, régions)
   - Import de données immobilières DVF (Demandes de Valeurs Foncières)

2. **Stockage distribué**:
   - **PostgreSQL/PostGIS**: Données géospatiales et transactions immobilières
   - **MongoDB**: Avis citoyens, sentiments et mots-clés
   - **Hadoop HDFS**: Stockage distribué des fichiers GeoJSON volumineux

3. **Traitement Big Data**:
   - **Apache Spark**: Traitement distribué (géospatial, NLP, agrégations)
   - **Hadoop Ecosystem**: Infrastructure de stockage et calcul distribué
   - **Pipeline ETL**: Extraction, transformation et chargement automatisés

4. **Couche applicative**:
   - **API REST Flask**: Endpoints optimisés avec cache et visualisations
   - **Frontend Streamlit**: Interface interactive avec cartes Leaflet
   - **Services de validation**: Contrôle qualité automatisé à chaque étape

## Prérequis

- **Docker et Docker Compose** (version récente)
- **Minimum 12 Go de RAM** disponible (recommandé 16 Go)
- **Environ 20 Go d'espace disque** (données + images Docker)
- **Processeur multi-cœurs** (minimum 4 cores pour Spark)
- **Réseau internet** pour le scraping et téléchargements

## Données traitées

- **34,455 communes** françaises avec géométries
- **54,656 avis citoyens** analysés
- **1,5M transactions immobilières** (fichier DVF 260MB)
- **368,672 mots-clés** extraits et analysés
- **Couverture géographique**: 18 régions, 101 départements

## Structure des Services

### Services de Base de Données
- **postgres**: PostgreSQL + PostGIS pour données géospatiales et immobilières
- **mongodb**: MongoDB pour avis, sentiments et mots-clés
- **mongodb-restore**: Service de restauration automatique des dumps

### Infrastructure Big Data
- **namenode**: Nœud maître Hadoop HDFS
- **datanode**: Nœud de stockage HDFS
- **hdfs-loader**: Chargement automatique des GeoJSON dans HDFS
- **spark-master**: Orchestrateur du cluster Spark
- **spark-worker / spark-worker-2**: Workers Spark (6 cores, 12GB RAM total)

### Services de Traitement
- **geo-data-importer**: Import des données géographiques GeoJSON → PostgreSQL
- **properties-importer**: Import des données immobilières DVF → PostgreSQL
- **avis-scraper**: Collecte des avis depuis "bien-dans-ma-ville.fr"
- **avis-processor-submitter**: Traitement NLP des avis avec Spark
- **data-aggregator**: Agrégation multi-niveaux (villes → départements → régions)

### Services d'Application
- **backend**: API REST Flask avec 8 endpoints
- **frontend**: Interface Streamlit avec cartes interactives

### Services de Validation
- **avis-data-validator**: Validation des données scrapées
- **avis-processor-validator**: Validation du traitement NLP
- **data-aggregator-validator**: Validation des agrégations statistiques

## Options de Déploiement

Deux options sont disponibles pour collecter les avis sur les villes:

1. **Exécuter le scraper** (long - environ 4h):
   - Collecte complète depuis le site source
   - Personnalisable (nombre de villes, mode test, etc.)

2. **Utiliser un dump MongoDB préexistant** (rapide):
   - Restaure directement une base de données déjà constituée
   - Évite le long processus de scraping

## Configuration du Projet

La configuration se fait via le fichier `.env` à la racine du projet:

```bash
# Configuration pour le scraping
ENABLE_SCRAPER=false      # Mettez 'true' pour activer le scraper, 'false' pour utiliser le dump
USE_MONGODB_DUMP=true     # Utilisé uniquement si ENABLE_SCRAPER=false

# Options du scraper (utilisées uniquement si ENABLE_SCRAPER=true)
MAX_VILLES=0           # 0 pour scraper toutes les villes, sinon limiter au nombre spécifié
MAX_WORKERS=8          # Nombre de workers pour le scraping parallèle
TEST_MODE=false        # Mode test avec seulement quelques villes
UPDATE_MODE=false      # Mode mise à jour (ne scrape que les nouvelles villes)
```

## Installation et Démarrage

1. **Clonez le dépôt**:
   ```bash
   git clone <url-du-repo>
   cd t-dat-902
   ```

2. **Configurez votre environnement**:
   - Créez un fichier `.env` à la racine du projet avec les paramètres souhaités
   - Vérifiez que le dump MongoDB est présent dans `avis-scraper/mongo-dump/villes_france/` si vous souhaitez l'utiliser

3. **Démarrez les services**:
   ```bash
   docker-compose up -d
   ```

4. **Suivez les logs pour surveiller le démarrage**:
   ```bash
   docker-compose logs -f
   ```

## Utilisation du Dump MongoDB

Si vous choisissez d'utiliser le dump MongoDB préexistant:

1. **Assurez-vous que vous avez le dump**:
   - Le dump doit être situé dans `avis-scraper/mongo-dump/villes_france/`
   - Les fichiers attendus sont: `avis.bson`, `avis.metadata.json`, `villes.bson`, `villes.metadata.json`

2. **Configurez les variables d'environnement**:
   ```
   ENABLE_SCRAPER=false
   USE_MONGODB_DUMP=true
   ```

3. **Démarrez les services**:
   ```bash
   docker-compose up -d
   ```

## Création d'un Dump MongoDB (pour partage)

Si vous avez déjà exécuté le scraper et souhaitez partager le résultat:

1. **Créez un dump de la base MongoDB**:
   ```bash
   docker exec -it mongodb mongodump --host localhost --port 27017 --username root --password rootpassword --authenticationDatabase admin --db villes_france --out /dump
   ```

2. **Copiez le dump depuis le conteneur**:
   ```bash
   mkdir -p avis-scraper/mongo-dump
   docker cp mongodb:/dump/villes_france avis-scraper/mongo-dump/
   ```

## Accès aux Services

Une fois le déploiement terminé, vous pouvez accéder aux services:

### Interfaces Web
- **🏠 Interface Streamlit**: http://localhost:8501 (Dashboard principal)
- **🔧 API Backend**: http://localhost:5001 (API REST + health check)
- **⚡ Spark Master UI**: http://localhost:8080 (Monitoring cluster Spark)
- **🗄️ Hadoop NameNode UI**: http://localhost:9870 (Monitoring HDFS)

### Bases de Données
- **📊 MongoDB**: `mongodb://root:rootpassword@localhost:27017/villes_france`
- **🗺️ PostgreSQL**: `postgresql://postgres:postgres@localhost:5432/gis_db`

### Endpoints API principaux
- `GET /api/v1/health` - Health check
- `GET /api/v1/map-areas/{zoom}/{bounds}` - Données cartographiques
- `GET /api/v1/price-tables` - Tableaux de prix immobiliers
- `GET /api/v1/sentiments/{entity}/{id}` - Graphiques de sentiment
- `GET /api/v1/word-clouds/{entity}/{id}` - Nuages de mots
- `GET /api/v1/area-details/{entity}/{id}` - Détails d'une zone

## Vérification de l'Installation

Pour vérifier que les données ont bien été chargées:

### Vérification MongoDB (Avis et Sentiments)
```bash
# Comptage des collections principales
docker exec mongodb mongosh --username root --password rootpassword --authenticationDatabase admin villes_france --eval "
  printjson({
    villes: db.villes.countDocuments({}),
    avis: db.avis.countDocuments({}),
    mots_villes: db.mots_villes.countDocuments({}),
    departements_stats: db.departements_stats.countDocuments({}),
    regions_stats: db.regions_stats.countDocuments({})
  })"
```
**Résultats attendus**: 34,455 villes, 54,656 avis, 34,455 mots_villes, 94 départements, 12 régions

### Vérification PostgreSQL (Géospatial et Immobilier)
```bash
# Comptage des tables principales
docker exec postgres psql -U postgres -d gis_db -c "
  SELECT 'cities' as table_name, COUNT(*) as count FROM cities
  UNION ALL SELECT 'departments', COUNT(*) FROM departments
  UNION ALL SELECT 'regions', COUNT(*) FROM regions
  UNION ALL SELECT 'properties', COUNT(*) FROM properties
  UNION ALL SELECT 'properties_cities_stats', COUNT(*) FROM properties_cities_stats;"
```
**Résultats attendus**: 34,945 cities, 101 departments, 18 regions, ~1.5M properties, 30,860 cities_stats

### Vérification HDFS (Stockage Distribué)
```bash
# Vérification des fichiers GeoJSON
docker exec namenode hdfs dfs -ls /data
docker exec namenode hdfs dfs -du -h /data
```
**Résultats attendus**: 3 fichiers GeoJSON (~10.5 MB total)

### Test de l'API Backend
```bash
# Test du health check
curl http://localhost:5001/api/v1/health

# Test des données cartographiques
curl "http://localhost:5001/api/v1/map-areas/10/48.5/2.0/49.0/2.5"
```

## Flux de Travail Complet

### Phase 1: Préparation des données
1. **hdfs-loader**: Chargement des GeoJSON (communes, départements, régions) dans HDFS
2. **mongodb-restore**: Restauration du dump MongoDB OU **avis-scraper**: Collecte des avis

### Phase 2: Import et traitement distribué
3. **geo-data-importer**: Import Spark des données géographiques HDFS → PostgreSQL
4. **properties-importer**: Import Spark des données DVF → PostgreSQL (1,5M transactions)
5. **avis-processor-submitter**: Traitement NLP Spark (sentiments + mots-clés)

### Phase 3: Agrégation et consolidation
6. **data-aggregator**: Calcul des statistiques par département et région
7. **Services de validation**: Contrôle qualité automatisé (3 validateurs)

### Phase 4: Exposition des données
8. **backend**: API REST Flask avec endpoints optimisés
9. **frontend**: Interface Streamlit avec visualisations interactives

### Dépendances critiques
```
BaseDB → Hadoop → Spark → Import → Aggregation → Validation → App
    ↓         ↓        ↓        ↓           ↓            ↓       ↓
PostGIS    HDFS   Workers   Data      Statistics    Quality  API/UI
MongoDB           3.4.1     Import    Multi-level   Control
```

## Dépannage

### Problèmes de mémoire (le plus fréquent)
```bash
# Arrêt complet et nettoyage
docker-compose down --volumes
docker system prune -a

# Vérification mémoire Docker
docker system df
docker stats --no-stream

# Augmentez la mémoire Docker à 12-16GB minimum
# Puis redémarrage
docker-compose up -d
```

### Problèmes de démarrage séquentiel
```bash
# Les services ont des dépendances strictes
# Si un service échoue, relancez dans l'ordre:
docker-compose up -d postgres mongodb
sleep 30
docker-compose up -d namenode datanode
sleep 30
docker-compose up -d spark-master spark-worker spark-worker-2
sleep 30
docker-compose up -d
```

### Diagnostic par service
```bash
# Logs détaillés par service critique
docker-compose logs -f hdfs-loader          # Chargement HDFS
docker-compose logs -f geo-data-importer     # Import géographique
docker-compose logs -f properties-importer   # Import immobilier
docker-compose logs -f avis-processor-submitter  # Traitement NLP
docker-compose logs -f data-aggregator       # Agrégations

# Status de tous les containers
docker-compose ps

# Utilisation des ressources
docker stats --no-stream
```

### Problèmes spécifiques

#### Spark Workers déconnectés
```bash
# Vérification du cluster Spark
curl http://localhost:8080/api/v1/applications
docker-compose restart spark-worker spark-worker-2
```

#### HDFS inaccessible
```bash
# Test de connectivité HDFS
docker exec namenode hdfs dfsadmin -report
docker exec namenode hdfs dfs -ls /
```

#### MongoDB corruption
```bash
# Réparation MongoDB
docker exec mongodb mongod --repair
docker-compose restart mongodb
```

#### PostgreSQL connexion refused
```bash
# Vérification PostgreSQL
docker exec postgres pg_isready -U postgres
docker exec postgres psql -U postgres -l
```

## Métriques et Performances

### Données traitées (Production)
- **Géospatiales**: 34,945 communes, 101 départements, 18 régions
- **Avis citoyens**: 54,656 avis analysés avec NLP
- **Immobilières**: 1,5M transactions DVF (260 MB de données)
- **Mots-clés**: 368,672 mots extraits et catégorisés
- **Agrégations**: 30,860 villes avec statistiques complètes

### Performance du cluster
- **Spark**: 2 workers, 6 cores total, 12 GB RAM
- **HDFS**: 10.5 MB stockés, réplication factor 3
- **Temps de traitement**: ~15-20 minutes pour pipeline complet
- **API**: <100ms pour requêtes géospatiales optimisées

### Métriques qualité
- **Completeness**: 98.5% (champs non-null)
- **Consistency**: 100% (cohérence inter-niveaux)
- **Accuracy**: 96.8% (données dans ranges attendus)
- **Prix réalistes**: 22,800/30,860 villes (74%) > 50k€

### Top villes par transactions immobilières
1. **Nice**: 4,604 transactions (354k€ moyen)
2. **Toulouse**: 4,430 transactions (291k€ moyen)  
3. **Nantes**: 2,672 transactions (294k€ moyen)

### Analyse sentiments (national)
- **Positif**: 36.15% des avis
- **Neutre**: 51.87% des avis
- **Négatif**: 11.99% des avis

## Architecture Technique Détaillée

### Stack technologique
- **Big Data**: Hadoop 3.2.1 + Spark 3.4.1
- **Bases de données**: PostgreSQL 14 + PostGIS, MongoDB latest
- **Backend**: Flask + Python 3.9
- **Frontend**: Streamlit + Leaflet.js
- **Containerisation**: Docker Compose avec 15+ services

### Patterns architecturaux
- **Microservices**: Services découplés avec responsabilités claires
- **Event-driven**: Pipeline ETL avec dépendances séquentielles
- **Clean Architecture**: Séparation couches données/métier/présentation
- **Validation multi-niveaux**: Contrôle qualité automatisé

## Arrêt du Projet

### Arrêt standard
```bash
docker-compose down
```

### Arrêt avec nettoyage complet (⚠️ perte de données)
```bash
docker-compose down --volumes
docker system prune -a
```

### Sauvegarde avant arrêt
```bash
# Dump MongoDB
docker exec mongodb mongodump --host localhost --port 27017 \
  --username root --password rootpassword --authenticationDatabase admin \
  --db villes_france --out /backup

# Export PostgreSQL
docker exec postgres pg_dump -U postgres gis_db > backup_postgres.sql
```