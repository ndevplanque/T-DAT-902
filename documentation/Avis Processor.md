# Documentation: Module Avis Processor

## Vue d'ensemble

Le module "Avis Processor" est un composant essentiel du projet de traitement des avis sur les villes françaises. Ce module est responsable de l'analyse textuelle des avis, de l'extraction des mots significatifs et de l'analyse de sentiment. Il transforme les données brutes des avis stockées dans MongoDB en informations exploitables pour la visualisation et l'analyse.

## Architecture

Le module "Avis Processor" est composé de deux services principaux:

1. **avis-processor-submitter**: Service principal qui effectue le traitement des avis
2. **avis-processor-validator**: Service de validation qui vérifie les résultats du traitement

### Structure des fichiers

```
avis-processor/
├── Dockerfile              # Configuration de l'environnement Docker
├── requirements.txt        # Dépendances Python
├── submit.sh               # Script de démarrage et d'orchestration
├── word_processor.py       # Script principal de traitement NLP
└── validation/
    ├── Dockerfile          # Environnement Docker pour la validation
    └── verify_processing.py # Script de vérification des résultats
```

## Fonctionnement technique

### Processus de traitement des avis (`word_processor.py`)

#### 1. Extraction des mots significatifs
- Utilise **SpaCy** avec le modèle français `fr_core_news_sm` pour l'analyse linguistique
- Implémente des filtres avancés pour éliminer les mots peu informatifs:
   - Liste personnalisée de stopwords supplémentaires
   - Filtrage par classe grammaticale (priorité aux noms, adjectifs et noms propres)
   - Normalisation des formes plurielles/singulières et dérivées

#### 2. Analyse de sentiment
- Classification des avis basée sur les notes:
   - Positif: note ≥ 4.0
   - Neutre: note entre 2.1 et 3.9
   - Négatif: note ≤ 2.0

#### 3. Traitement des données
- Analyse ville par ville avec MongoDB
- Extraction des mots les plus significatifs (top 150)
- Calcul des pourcentages de sentiment pour chaque ville

### Processus de validation (`verify_processing.py`)

- Génère des statistiques globales sur le traitement
- Identifie les villes avec les sentiments les plus positifs/négatifs
- Analyse les mots les plus fréquents à l'échelle nationale
- Vérifie la cohérence entre les mots extraits et les sentiments
- Crée des visualisations et rapports de synthèse

## Configuration et utilisation

### Variables d'environnement

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `MONGO_URI` | URI de connexion à MongoDB | `mongodb://root:rootpassword@mongodb:27017/` |
| `MONGO_DB` | Nom de la base de données | `villes_france` |
| `WAIT_FOR_SCRAPER` | Attend que le scraper ait ajouté des données | `true` |
| `OUTPUT_DIR` | Répertoire de sortie pour les résultats de validation | `/app/results` |

### Intégration avec Docker Compose

Le service s'intègre au projet global via docker-compose.yml:

```yaml
# Service pour exécuter le traitement des avis
avis-processor-submitter:
  build:
    context: ./avis-processor
    dockerfile: Dockerfile
  container_name: avis-processor-submitter
  restart: on-failure
  environment:
    - MONGO_URI=mongodb://root:rootpassword@mongodb:27017/
    - MONGO_DB=villes_france
    - WAIT_FOR_SCRAPER=${ENABLE_SCRAPER:-true}
  depends_on:
    - mongodb
    - avis-scraper
  volumes:
    - ./avis-processor:/app
    - ./logs:/app/logs
  networks:
    - t-dat-902-network

# Service de validation des données traitées
avis-processor-validator:
  build:
    context: ./avis-processor/validation
    dockerfile: Dockerfile
  container_name: avis-processor-validator
  volumes:
    - ./avis-processor/validation:/app
    - ./logs:/app/logs
    - ./avis-processor/validation/results:/app/results
  environment:
    - MONGO_URI=mongodb://root:rootpassword@mongodb:27017/
    - MONGO_DB=villes_france
    - OUTPUT_DIR=/app/results
  networks:
    - t-dat-902-network
  depends_on:
    - mongodb
    - avis-processor-submitter
```

## Workflow d'exécution

1. Le service `avis-processor-submitter` démarre après les services MongoDB et avis-scraper
2. Le script `submit.sh` vérifie la disponibilité de MongoDB
3. Si `WAIT_FOR_SCRAPER=true`, il attend que des données soient présentes dans la collection `villes`
4. Le script `word_processor.py` est exécuté pour traiter les avis
5. Pour chaque ville non traitée:
   - Extraction des mots significatifs des avis
   - Analyse des sentiments
   - Stockage des résultats dans la collection `mots_villes`
   - Mise à jour du statut de traitement
6. Le service `avis-processor-validator` vérifie ensuite les résultats et génère des rapports

## Résultats du traitement

Les résultats sont stockés dans deux endroits:

1. **MongoDB** (collection `mots_villes`) avec la structure:
   ```json
   {
     "city_id": "ID_VILLE",
     "ville_nom": "NOM_VILLE",
     "mots": [
       {"mot": "commerce", "poids": 15},
       {"mot": "transport", "poids": 10},
       ...
     ],
     "sentiments": {
       "positif": 25,
       "neutre": 15,
       "negatif": 10,
       "positif_percent": 50.0,
       "neutre_percent": 30.0,
       "negatif_percent": 20.0
     },
     "date_extraction": "2025-04-10T12:34:56"
   }
   ```

2. **Rapports de validation** (générés dans `/app/results`):
   - `stats_summary.json`: Statistiques globales du traitement
   - `top_villes_positives.csv`: Top 5 des villes les plus positives
   - `top_villes_negatives.csv`: Top 5 des villes les plus négatives
   - `top_50_mots_frequents.csv`: 50 mots les plus fréquents
   - `distribution_sentiment_positif.png`: Graphique de distribution
   - `top30_mots_frequents.png`: Graphique des 30 mots les plus fréquents
   - `rapport_synthese.txt`: Synthèse complète du traitement

## Dépendances techniques

- **Python 3.9**
- **SpaCy** avec le modèle français `fr_core_news_sm`
- **pymongo** pour l'interaction avec MongoDB
- **pandas**, **matplotlib**, **seaborn** pour l'analyse et la visualisation
- **tabulate** pour la mise en forme des résultats

## Utilisation dans le projet global

Le module "Avis Processor" doit être exécuté après le scraping des avis et avant la visualisation frontend. Il fournit les données traitées nécessaires pour générer des nuages de mots et des analyses de sentiment utilisés par l'interface utilisateur.

Pour démarrer uniquement cette partie du projet:

```bash
docker-compose up -d mongodb avis-processor-submitter avis-processor-validator
```