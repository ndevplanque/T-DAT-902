# Backend - API Flask REST

## Vue d'ensemble

Le backend de Homepedia est une API REST développée en Flask qui sert d'interface entre les données géospatiales (PostgreSQL/PostGIS) et les avis textuels (MongoDB) pour l'application frontend Streamlit. Il fournit des endpoints pour la visualisation cartographique, l'analyse de sentiment et la génération de nuages de mots.

## Architecture technique

### Technologies utilisées

- **Framework**: Flask (Python 3.9)
- **Base de données**: PostgreSQL avec PostGIS + MongoDB
- **Drivers**: psycopg2-binary (PostgreSQL), pymongo (MongoDB)
- **Visualisations**: matplotlib (graphiques), wordcloud (nuages de mots)
- **Tests**: pytest avec couverture de code
- **Containerisation**: Docker avec support développement

### Structure du code

```
backend/
├── api/
│   ├── main.py                 # Point d'entrée Flask + routing
│   ├── logs.py                 # Configuration logging
│   └── v1/                     # API versionnée v1
│       ├── database/           # Couche d'accès aux données
│       │   ├── mongodb.py      # Connexion MongoDB
│       │   ├── postgres.py     # Connexion PostgreSQL
│       │   └── queries.py      # Requêtes SQL centralisées
│       ├── features/           # Fonctionnalités métier
│       │   ├── health/         # Health check
│       │   ├── map_areas/      # Données géospatiales
│       │   ├── area_listing/   # Listing zones avec prix réels
│       │   ├── area_transactions/ # Transactions immobilières détaillées
│       │   ├── area_details/   # Détails zones
│       │   ├── databases/      # Introspection bases de données
│       │   ├── sentiments/     # Analyse sentiment
│       │   └── word_clouds/    # Nuages de mots
│       └── models/             # Modèles de données
├── tests/                      # Tests unitaires
├── requirements.txt            # Dépendances Python
└── Dockerfile                  # Configuration container
```

## Endpoints API

### API v1 (/api/v1)

1. **GET /health** - Health check de l'API
   - **Réponse**: `{"success": true}`

2. **GET /map-areas/{zoom}/{sw_lat}/{sw_lon}/{ne_lat}/{ne_lon}** - Données cartographiques
   - **Paramètres**: Niveau de zoom et coordonnées du viewport
   - **Logique**: 
     - Zoom > 9: Retourne les villes
     - Zoom 7-9: Retourne les départements  
     - Zoom ≤ 6: Retourne les régions
   - **Réponse**: GeoJSON avec géométries et métadonnées

3. **GET /area-listing** - Listing des zones avec données immobilières réelles
   - **Réponse**: Liste complète régions/départements/villes avec statistiques prix
   - **Données**: Prix min/max/moyenne, nombre de transactions depuis 2014
   - **Filtrage**: Exclusion arrondissements Paris/Marseille (éviter doublons)
   - **Format**: `{"regions": [...], "departments": [...], "cities": [...]}`

4. **GET /sentiments/{entity}/{id}** - Image d'analyse de sentiment
   - **Paramètres**: entity (cities uniquement), id numérique
   - **Réponse**: Image PNG binaire (graphique donut) générée par matplotlib
   - **Content-Type**: image/png
   - **Données**: Pourcentages positif/négatif/neutre des avis MongoDB

5. **GET /word-clouds/{entity}/{id}** - Image nuage de mots
   - **Paramètres**: entity (cities uniquement), id numérique
   - **Réponse**: Image PNG binaire générée par wordcloud
   - **Content-Type**: image/png
   - **Source**: Fréquences mots de la collection `mots_villes`

6. **GET /area-details/{entity}/{id}** - Détails complets d'une zone
   - **Réponse**: Informations complètes (nom, population, avis, etc.)

7. **GET /area-transactions/{entity}/{id}** - Transactions immobilières détaillées
   - **Paramètres**: entity (cities uniquement), id numérique
   - **Réponse**: Liste transactions individuelles avec dates, prix, surfaces
   - **Spécial**: Agrégation automatique Paris (75056→75101-75120) et Marseille (13055→13201-13216)
   - **Filtrage**: Données aberrantes < 500€ exclues
   - **Tri**: Par date décroissante

8. **GET /postgres/schema** - Schéma base PostgreSQL
   - **Réponse**: Structure tables avec exemples et définitions colonnes

9. **GET /mongodb/schema** - Schéma de la base MongoDB
   - **Réponse**: Structure des collections et champs

## Connexions aux bases de données

### PostgreSQL (PostGIS)

```python
class Postgres:
    - Host: host.docker.internal:5432  # Configuration Docker
    - Database: gis_db
    - Utilisateur: postgres/postgres
    - Features: Context manager, autocommit, gestion erreurs
    - Schema introspection: Méthode schema() disponible
```

**Tables utilisées**:
- `cities`: Géométries des villes
- `departments`: Géométries des départements  
- `regions`: Géométries des régions
- `properties`: Transactions immobilières individuelles (DVF)
- `properties_cities_stats`: Statistiques pré-calculées par ville
- `properties_departments_stats`: Statistiques pré-calculées par département
- `properties_regions_stats`: Statistiques pré-calculées par région

### MongoDB

```python
class MongoDB:
    - URI: mongodb://root:rootpassword@host.docker.internal:27017  # Configuration Docker
    - Database: villes_france
    - Features: Context manager, conversion ObjectId, filtrage champs
```

**Collections utilisées**:
- `villes`: Informations villes + avis agrégés
- `mots_villes`: Fréquences mots + scores sentiment
- `avis`: Avis individuels détaillés

## Architecture des fonctionnalités

Chaque fonctionnalité suit le pattern **Service-Repository**:

```
features/feature_name/
├── service.py      # Logique métier + validation
└── repository.py   # Accès aux données
```

### Exemple: Map Areas

```python
# Service: Détermine le type d'entité selon le zoom
# Repository: Requête PostGIS avec ST_Intersects + JOIN statistiques
# Résultat: GeoJSON avec données prix réelles intégrées
```

### Exemple: Area Listing  

```python
# Service: Agrège données des 3 niveaux géographiques
# Repository: Requêtes optimisées sur tables statistiques
# Résultat: Listing complet avec prix min/max/moyenne par zone
```

### Exemple: Area Transactions

```python
# Service: Gestion spéciale Paris/Marseille + filtrage qualité
# Repository: Requêtes sur table properties avec agrégations
# Résultat: Transactions individuelles triées par date
```

### Exemple: Sentiments

```python
# Service: Génère graphique matplotlib depuis données MongoDB
# Repository: Récupère scores sentiment par ville
# Résultat: Image PNG prête pour affichage
```

## Gestion des erreurs

- **Handler global**: Capture toutes les exceptions HTTP
- **Format standard**: `{"error": "message", "code": 500}`
- **Logging**: Erreurs tracées avec détails technique
- **Codes supportés**: 404, 500, erreurs base de données

## Configuration

### Variables d'environnement

```bash
FLASK_APP=api/main.py
FLASK_ENV=development
FLASK_DEBUG=1
```

### Docker

```yaml
services:
  backend:
    build: ./backend
    ports: ["5001:5001"]
    volumes: ["./backend:/app"]
    depends_on: [postgres]
```

## Tests

### Configuration pytest

```ini
[tool:pytest]
pythonpath = api
testpaths = tests
addopts = --cov=api --cov-report=term-missing
```

### Types de tests

1. **Tests unitaires**: Services et repositories isolés
2. **Tests d'intégration**: Endpoints Flask avec mocking
3. **Tests de données**: Connexions PostgreSQL/MongoDB
4. **Fixtures**: Client Flask, données mockées

### Commandes

```bash
# Tests complets avec couverture
docker compose exec backend pytest

# Tests d'une fonctionnalité spécifique
docker compose exec backend pytest tests/api/v1/features/health/

# Rapport de couverture HTML
docker compose exec backend pytest --cov-report=html
```

## Performance et optimisations

### Requêtes géospatiales

- **Index spatiaux**: Utilisation optimale des index PostGIS
- **ST_Intersects**: Requêtes géographiques optimisées
- **Zoom adaptatif**: Granularité des données selon le niveau

### Génération d'images

- **Cache mémoire**: Images générées à la demande
- **Format optimisé**: PNG optimisé pour le web
- **Taille fixe**: Dimensions standardisées (300x200px)

## Intégration données immobilières réelles

### Source des données
- **DVF (Demandes de Valeurs Foncières)**: Données officielles transactions immobilières
- **Période**: 2014 à aujourd'hui
- **Couverture**: France métropolitaine complète

### Traitement des données
- **Filtrage qualité**: Exclusion transactions < 500€ (données aberrantes)
- **Agrégation géographique**: Calculs automatiques min/max/moyenne par zone
- **Gestion spéciale**: Paris et Marseille (consolidation arrondissements)
- **Statistiques pré-calculées**: Tables optimisées pour performances

### Architecture statistiques
```sql
-- Exemple structure table statistiques
properties_cities_stats:
- city_id: Identifiant ville
- transactions_count: Nombre de transactions
- min_price_per_m2: Prix minimum par m²
- max_price_per_m2: Prix maximum par m²
- avg_price_per_m2: Prix moyen par m²
```

## Limitations actuelles

1. **Credentials hardcodés**: Configuration BDD dans le code
2. **Sentiments/word-clouds villes uniquement**: Départements/régions non implémentés
3. **Transactions villes uniquement**: Départements/régions non implémentés  
4. **Pas de cache**: Régénération images PNG à chaque requête
5. **Authentification**: Aucune sécurité d'accès
6. **Monitoring**: Logging basique sans métriques
7. **Host configuration**: Utilise host.docker.internal (spécifique Docker Desktop)

## Évolutions futures

1. **Configuration externalisée**: Variables d'environnement
2. **Cache Redis**: Mise en cache des images et requêtes
3. **Authentification JWT**: Sécurisation des endpoints
4. **Transactions départements/régions**: Extension endpoint area-transactions
5. **Monitoring**: Métriques et alertes applicatives
6. **Rate limiting**: Protection contre le spam
7. **API pagination**: Gestion grandes listes de transactions
8. **Données temps réel**: Mise à jour automatique DVF

## Dépendances

### Production

```txt
Flask==2.3.3
Flask-CORS==4.0.0
psycopg2-binary==2.9.7
pymongo==4.5.0
numpy==1.24.3
matplotlib==3.7.2
wordcloud==1.9.2
plotly
```

### Développement

```txt
pytest==7.4.2
pytest-mock==3.11.1
pytest-cov==4.1.0
```

Le backend Flask constitue le cœur de l'architecture Homepedia, orchestrant l'accès aux données géospatiales et textuelles pour fournir une API REST cohérente et performante au frontend Streamlit.