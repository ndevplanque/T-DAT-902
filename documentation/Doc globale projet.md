# Documentation du Projet t-dat-902

## Introduction

Ce projet constitue une infrastructure complète pour le traitement de données géographiques et d'avis sur les villes françaises. Il combine plusieurs technologies pour collecter, stocker, traiter et visualiser ces données.

## Architecture du Projet

Le projet s'organise autour de plusieurs composants interconnectés:

1. **Collecte de données**:
   - Scraping d'avis sur les villes françaises depuis le site "bien-dans-ma-ville.fr"
   - Import de données géographiques (communes, départements, régions)

2. **Stockage**:
   - PostgreSQL avec extension PostGIS pour les données géospatiales
   - MongoDB pour les avis sur les villes

3. **Traitement de données**:
   - Framework Hadoop/HDFS pour le stockage distribué
   - Spark pour le traitement parallèle des données

4. **Interface utilisateur**:
   - Backend Flask pour l'API
   - Frontend Streamlit pour la visualisation

## Prérequis

- Docker et Docker Compose
- Au moins 8 Go de RAM disponible
- Environ 10 Go d'espace disque

## Structure des Services

### Services de Base de Données
- **PostgreSQL (PostGIS)**: Stockage des données géographiques
- **MongoDB**: Stockage des avis sur les villes

### Services Hadoop/Spark
- **Namenode & Datanode**: Infrastructure HDFS
- **Spark Master & Workers**: Traitement distribué
- **HDFS Loader**: Import des fichiers GeoJSON dans HDFS

### Services d'Application
- **Backend**: API Flask
- **Frontend**: Interface Streamlit
- **Geo Data Importer**: Import des données géographiques
- **Avis Scraper**: Collecte des avis de villes
- **Avis Processor**: Traitement des avis avec Spark

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

- **Interface Streamlit**: http://localhost:8501
- **API Backend**: http://localhost:5001
- **Spark Master UI**: http://localhost:8080
- **Hadoop NameNode UI**: http://localhost:9870
- **MongoDB**: mongodb://root:rootpassword@localhost:27017
- **PostgreSQL**: postgresql://postgres:postgres@localhost:5432/gis_db

## Vérification de l'Installation

Pour vérifier que les données ont bien été chargées:

- **Vérification des données MongoDB**:
  ```bash
  docker exec -it mongodb mongosh --username root --password rootpassword --authenticationDatabase admin villes_france --eval "db.villes.countDocuments({}); db.avis.countDocuments({})"
  ```

- **Vérification des données PostgreSQL**:
  ```bash
  docker exec -it postgres psql -U postgres -d gis_db -c "SELECT COUNT(*) FROM cities; SELECT COUNT(*) FROM departments; SELECT COUNT(*) FROM regions;"
  ```

## Flux de Travail

1. Les données géographiques (GeoJSON) sont chargées dans HDFS
2. Les avis de villes sont soit scrapés, soit restaurés depuis un dump
3. Le service `geo-data-importer` importe les données géographiques dans PostgreSQL
4. Le service `avis-processor-submitter` traite les avis avec Spark
5. Le backend expose les données via une API
6. Le frontend Streamlit présente les données sous forme visuelle

## Dépannage

### Problèmes de mémoire
Si vous rencontrez des problèmes liés à la mémoire:
```bash
docker-compose down
docker system prune -a
# Augmentez la mémoire allouée à Docker dans les paramètres
docker-compose up -d
```

### Logs des services
Pour consulter les logs d'un service spécifique:
```bash
docker-compose logs -f [service]
```
Exemples: `docker-compose logs -f avis-scraper`, `docker-compose logs -f mongodb-restore`

### Redémarrage d'un service
Si un service particulier pose problème:
```bash
docker-compose restart [service]
```

## Arrêt du Projet

Pour arrêter tous les services:
```bash
docker-compose down
```

Pour arrêter et supprimer les volumes (attention, perte de données):
```bash
docker-compose down -v
```