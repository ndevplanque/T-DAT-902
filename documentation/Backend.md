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
│       │   ├── price_tables/   # Tableaux prix immobiliers
│       │   ├── sentiments/     # Analyse sentiment
│       │   ├── word_clouds/    # Nuages de mots
│       │   ├── area_details/   # Détails zones
│       │   └── mongodb/        # Introspection MongoDB
│       └── models/             # Modèles de données
├── tests/                      # Tests unitaires
├── requirements.txt            # Dépendances Python
└── Dockerfile                  # Configuration container
```

## Endpoints API

### API v1 (/api/v1)

1. **GET /health** - Health check de l'API
   - **Réponse**: `{"status": "healthy", "timestamp": "..."}`

2. **GET /map-areas/{zoom}/{sw_lat}/{sw_lon}/{ne_lat}/{ne_lon}** - Données cartographiques
   - **Paramètres**: Niveau de zoom et coordonnées du viewport
   - **Logique**: 
     - Zoom > 9: Retourne les villes
     - Zoom 7-9: Retourne les départements  
     - Zoom ≤ 6: Retourne les régions
   - **Réponse**: GeoJSON avec géométries et métadonnées

3. **GET /price-tables** - Tableaux de prix immobiliers
   - **Réponse**: Prix moyens par m² pour régions/départements/villes
   - **Note**: Données simulées (1500-6000€/m²)

4. **GET /sentiments/{entity}/{id}** - Graphique d'analyse de sentiment
   - **Paramètres**: entity (cities/departments/regions), id numérique
   - **Réponse**: Image PNG (graphique donut) générée par matplotlib
   - **Données**: Pourcentages positif/négatif/neutre des avis

5. **GET /word-clouds/{entity}/{id}** - Nuage de mots
   - **Paramètres**: entity (cities/departments/regions), id numérique
   - **Réponse**: Image PNG (300x200px) générée par wordcloud
   - **Source**: Fréquences mots de la collection `mots_villes`

6. **GET /area-details/{entity}/{id}** - Détails complets d'une zone
   - **Réponse**: Informations complètes (nom, population, avis, etc.)

7. **GET /mongodb/schema** - Schéma de la base MongoDB
   - **Réponse**: Structure des collections et champs

## Connexions aux bases de données

### PostgreSQL (PostGIS)

```python
class Postgres:
    - Host: host.docker.internal:5432
    - Database: gis_db
    - Utilisateur: postgres/postgres
    - Features: Context manager, autocommit, gestion erreurs
```

**Tables utilisées**:
- `cities`: Géométries des villes
- `departments`: Géométries des départements  
- `regions`: Géométries des régions
- `properties`: Données immobilières (en développement)

### MongoDB

```python
class MongoDB:
    - URI: mongodb://root:rootpassword@host.docker.internal:27017
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
# Repository: Requête PostGIS avec ST_Intersects
# Résultat: GeoJSON optimisé pour l'affichage carte
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

## Limitations actuelles

1. **Credentials hardcodés**: Configuration BDD dans le code
2. **Prix simulés**: Pas d'intégration données immobilières réelles  
3. **Pas de cache**: Régénération images à chaque requête
4. **Authentification**: Aucune sécurité d'accès
5. **Monitoring**: Logging basique sans métriques

## Évolutions futures

1. **Configuration externalisée**: Variables d'environnement
2. **Cache Redis**: Mise en cache des images et requêtes
3. **Authentification JWT**: Sécurisation des endpoints
4. **Données réelles**: Intégration vraies données DVF
5. **Monitoring**: Métriques et alertes applicatives
6. **Rate limiting**: Protection contre le spam

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
```

### Développement

```txt
pytest==7.4.2
pytest-mock==3.11.1
pytest-cov==4.1.0
```

Le backend Flask constitue le cœur de l'architecture Homepedia, orchestrant l'accès aux données géospatiales et textuelles pour fournir une API REST cohérente et performante au frontend Streamlit.