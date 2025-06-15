# Validation Services - Système de contrôle qualité

## Vue d'ensemble

Les services de validation de Homepedia constituent un système complet de contrôle qualité à trois niveaux qui assure l'intégrité, la cohérence et la fiabilité des données tout au long du pipeline de traitement. Chaque service de validation s'exécute automatiquement après son service principal correspondant et génère des rapports détaillés avec métriques et visualisations.

## Architecture de validation

### Services de validation disponibles

```
Validation Pipeline
├── avis-data-validator         # Validation données scrapées
│   └── Contrôle: Complétude et cohérence des avis
├── avis-processor-validator    # Validation traitement NLP
│   └── Contrôle: Sentiments et extraction de mots
└── data-aggregator-validator   # Validation agrégations
    └── Contrôle: Cohérence statistique multi-niveaux
```

### Orchestration et dépendances

```yaml
# Ordre d'exécution dans docker-compose.yml
Services principaux → Services de validation → Rapports
avis-scraper → avis-data-validator
avis-processor → avis-processor-validator  
data-aggregator → data-aggregator-validator
```

## Avis Data Validator

### Responsabilités principales

- **Validation complétude**: Vérification des champs obligatoires
- **Contrôle cohérence**: Validation des références entre collections
- **Analyse qualité**: Métriques sur la distribution des données
- **Détection anomalies**: Identification des incohérences de notes

### Configuration Docker

```yaml
avis-data-validator:
  build:
    context: ./avis-scraper/validation
    dockerfile: Dockerfile
  container_name: avis-data-validator
  volumes:
    - ./avis-scraper/validation:/app
    - ./logs:/app/logs
  environment:
    - MONGO_URI=mongodb://root:rootpassword@mongodb:27017/
    - MONGO_DB=villes_france
  depends_on:
    - mongodb
    - avis-scraper
```

### Types de contrôles effectués

#### Validation de complétude

Contrôles de présence des champs obligatoires:
- **Villes**: Vérification de 8 champs essentiels (nom, codes, identifiants, URL, notes)
- **Avis**: Validation de 8 champs critiques (identifiants, auteur, date, notes, description)
- **Détection automatique**: Identification des champs manquants ou null
- **Reporting détaillé**: Liste précise des champs défaillants par enregistrement

#### Validation de cohérence

Vérification de la logique métier et calculs:
- **Recalcul automatique**: Comparaison entre moyennes calculées et stockées
- **Seuil de tolérance**: Détection d'écarts > 0.5 point sur les notes
- **Validation croisée**: Cohérence entre notes détaillées et moyennes globales
- **Identification précise**: Localisation des villes avec incohérences de calcul

### Métriques générées

**Statistiques globales**:
- 34,455 villes analysées
- 54,656 avis collectés
- 28,978 villes sans avis (84%)
- 0 ville avec notes incohérentes ✅

**Distribution des avis**:
- Moyenne: 1.6 avis par ville
- Maximum: 47 avis (ville la plus active)
- Top 10 villes par volume d'avis

### Sorties de validation

**validation_results.json**: Rapport JSON structuré contenant:
- **Statistiques globales**: Totaux villes, avis, moyennes par ville
- **Détection d'anomalies**: Avis orphelins, notes incohérentes, champs manquants
- **Classements**: Top 10 des villes par volume d'avis
- **Métriques qualité**: Indicateurs de complétude et cohérence

## Avis Processor Validator

### Responsabilités principales

- **Validation traitement Spark**: Vérification du succès du traitement
- **Contrôle sentiments**: Validation des pourcentages d'analyse de sentiment
- **Analyse lexicale**: Vérification de l'extraction des mots-clés
- **Génération rapports**: Création de visualisations et statistiques

### Configuration Docker

```yaml
avis-processor-validator:
  build:
    context: ./avis-processor/validation
    dockerfile: Dockerfile
  container_name: avis-processor-validator
  volumes:
    - ./avis-processor/validation:/app
    - ./avis-processor/validation/results:/app/results
  environment:
    - MONGO_URI=mongodb://root:rootpassword@mongodb:27017/
    - MONGO_DB=villes_france
    - OUTPUT_DIR=/app/results
  depends_on:
    - avis-processor-submitter
```

### Types de contrôles effectués

#### Validation du traitement Spark

Contrôle de l'exécution complète du pipeline Spark:
- **Comptage exhaustif**: Vérification du traitement de toutes les villes
- **Statut de traitement**: Validation du marquage "traité" pour chaque ville
- **Calcul de couverture**: Pourcentage de villes traitées avec succès
- **Détection d'échecs**: Identification des villes non traitées

#### Validation des sentiments

Contrôle de la qualité de l'analyse de sentiment:
- **Validation mathématique**: Vérification que positif + neutre + négatif = 100%
- **Seuil de tolérance**: Détection d'écarts > 0.1% dans les pourcentages
- **Collecte statistique**: Agrégation des distributions de sentiment par ville
- **Alertes automatiques**: Signalement des incohérences détectées

### Métriques générées

**Traitement global**:
- 34,455 villes traitées (100% succès)
- 368,672 mots extraits
- Moyenne: 35.61 mots par ville

**Analyse de sentiment**:
- Positif moyen: 36.15%
- Neutre moyen: 51.87%
- Négatif moyen: 11.99%

### Sorties de validation

**stats_summary.json**: Métriques de performance globales
**rapport_synthese.txt**: Résumé textuel automatique
**top_villes_positives.csv**: Classement des villes les mieux notées
**top_50_mots_frequents.csv**: Analyse lexicale complète

**Visualisations générées**:
- `distribution_sentiment_positif.png`: Histogramme des sentiments
- `top30_mots_frequents.png`: Graphique des mots-clés principaux

## Data Aggregator Validator

### Responsabilités principales

- **Validation MongoDB**: Cohérence des agrégations d'avis
- **Validation PostgreSQL**: Cohérence des agrégations immobilières
- **Contrôle multi-niveaux**: Villes → Départements → Régions
- **Génération dashboards**: Visualisations automatiques

### Configuration Docker

```yaml
data-aggregator-validator:
  build:
    context: ./data-aggregator/validation
    dockerfile: Dockerfile.validator
  container_name: data-aggregator-validator
  restart: "no"
  environment:
    - MONGO_URI=mongodb://root:rootpassword@mongodb:27017/
    - MONGO_DB=villes_france
    - POSTGRES_HOST=postgres
    - OUTPUT_DIR=/app/results
  volumes:
    - ./data-aggregator/validation/results:/app/results
  depends_on:
    - data-aggregator
```

### Scripts de validation

#### 1. Validation agrégations MongoDB (aggregation_validator.py)

Contrôle de cohérence des agrégations départementales:
- **Recalcul automatique**: Vérification des totaux villes et avis par département
- **Validation des compteurs**: Comparaison entre agrégations et sources
- **Contrôle d'échelle**: Validation des notes sur l'échelle 0-10
- **Détection d'erreurs**: Identification précise des incohérences avec contexte
- **Seuils de tolérance**: Écart maximal de 1 avis accepté

#### 2. Validation propriétés PostgreSQL (properties_aggregation_validator.py)

Contrôle de qualité des données immobilières:
- **Validation logique**: Détection des prix négatifs ou nuls
- **Seuils de réalisme**: Identification des prix < 10k€ ou > 2M€
- **Analyse de distribution**: Contrôle des prix > 50k€ (seuil de cohérence)
- **Détection d'outliers**: Identification automatique des valeurs aberrantes
- **Métriques de qualité**: Calcul de pourcentages de données valides

### Métriques générées

#### Validation avis (MongoDB)

**Départements**:
- 94 départements agrégés
- 54,656 avis consolidés
- 0 incohérence détectée ✅

**Top départements par note**:
1. Hautes-Alpes (05): 3.7/5
2. Ille-et-Vilaine (35): 3.7/5
3. Morbihan (56): 3.6/5

#### Validation propriétés (PostgreSQL)

**Qualité des prix**:
- 0 prix négatif détecté ✅
- 22,800/30,860 villes (74%) avec prix > 50k€
- Prix moyen national: 150,681€

**Top villes transactions**:
1. Nice: 4,604 transactions (354k€ moyen)
2. Toulouse: 4,430 transactions (291k€ moyen)
3. Nantes: 2,672 transactions (294k€ moyen)

### Visualisations générées

**Dashboards automatiques**:
- `prix_regions.png`: Cartographie des prix par région
- `prix_vs_transactions_departements.png`: Corrélation volume/prix
- `distribution_surfaces.png`: Histogrammes surfaces immobilières
- `sentiments_regions.png`: Heatmap des sentiments par région
- `relation_avis_notes.png`: Corrélation volume d'avis/qualité

## Orchestration et intégration

### Script d'orchestration

Script maître de validation complète du pipeline:
1. **Validation séquentielle**: Exécution ordonnée des validations d'avis et immobilières
2. **Consolidation**: Génération d'un rapport final unifié
3. **Logging intégré**: Messages de progression et statuts
4. **Centralisation**: Collecte de tous les rapports dans un répertoire unique
5. **Vérification finale**: Confirmation de succès avec liens vers résultats

### Intégration avec le monitoring

Génération de métriques pour surveillance continue:
- **Horodatage**: Timestamp précis pour historisation
- **Compteurs sources**: Volumes de données collectées par source
- **Scores de qualité**: Indicateurs quantifiés (complétude, cohérence, précision)
- **Détection d'anomalies**: Comptage des problèmes par catégorie
- **Format JSON**: Structure standardisée pour intégration monitoring

## Points forts du système

### Validation exhaustive

1. **Multi-niveaux**: Contrôle à chaque étape du pipeline
2. **Multi-sources**: Validation MongoDB et PostgreSQL
3. **Automatisée**: Exécution sans intervention manuelle
4. **Traçable**: Logs détaillés et historisation

### Détection proactive

1. **Anomalies métier**: Prix aberrants, sentiments incohérents
2. **Problèmes techniques**: Échecs de traitement, données manquantes
3. **Incohérences**: Totaux non concordants entre niveaux
4. **Alertes visuelles**: Graphiques pour détection rapide

### Reporting complet

1. **Métriques JSON**: Intégration monitoring/alerting
2. **Rapports HTML**: Dashboards pour analyse humaine
3. **Visualisations PNG**: Graphiques pour présentations
4. **Logs structurés**: Debugging et audit

Le système de validation de Homepedia garantit la fiabilité et la qualité des données servies par l'API, constituant un filet de sécurité essentiel pour la crédibilité de la plateforme d'analyse immobilière et urbaine.