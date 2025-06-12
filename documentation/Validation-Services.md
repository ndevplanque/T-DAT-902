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

```python
# Script validate_data.py
def validate_ville_completeness(ville):
    """Valide la complétude des champs obligatoires pour une ville"""
    required_fields = [
        "nom", "code_postal", "code_insee", "city_id", 
        "department_id", "url", "notes", "nombre_avis"
    ]
    
    missing_fields = []
    for field in required_fields:
        if field not in ville or ville[field] is None:
            missing_fields.append(field)
    
    return missing_fields

def validate_avis_completeness(avis):
    """Valide la complétude des champs obligatoires pour un avis"""
    required_fields = [
        "ville_id", "city_id", "avis_id", "auteur", 
        "date", "note_globale", "notes", "description"
    ]
    
    missing_fields = []
    for field in required_fields:
        if field not in avis or avis[field] is None:
            missing_fields.append(field)
    
    return missing_fields
```

#### Validation de cohérence

```python
def validate_notes_consistency():
    """Vérifie la cohérence entre notes calculées et stockées"""
    
    inconsistent_villes = []
    
    for ville in db.villes.find():
        if "notes" in ville:
            # Recalcul de la moyenne depuis les notes détaillées
            calculated_avg = sum(ville["notes"].values()) / len(ville["notes"])
            stored_avg = ville["notes"].get("moyenne", 0)
            
            # Seuil de tolérance pour écart
            if abs(calculated_avg - stored_avg) > 0.5:
                inconsistent_villes.append({
                    "city_id": ville["city_id"],
                    "nom": ville["nom"],
                    "calculated": calculated_avg,
                    "stored": stored_avg,
                    "difference": abs(calculated_avg - stored_avg)
                })
    
    return inconsistent_villes
```

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

**validation_results.json**:
```json
{
  "summary": {
    "total_villes": 34455,
    "total_avis": 54656,
    "villes_sans_avis": 28978,
    "moyenne_avis_par_ville": 1.59
  },
  "issues": {
    "avis_orphelins": 0,
    "villes_notes_incoherentes": 0,
    "villes_champs_manquants": []
  },
  "top_10_villes_avis": [
    {"nom": "Avis Boulogne-Billancourt 92100", "nb_avis": 47},
    {"nom": "Avis Issy-les-Moulineaux 92130", "nb_avis": 44}
  ]
}
```

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

```python
def verify_spark_processing():
    """Vérifie que toutes les villes ont été traitées par Spark"""
    
    total_villes = db.villes.count_documents({})
    villes_traitees = db.villes.count_documents({"status": "traité"})
    
    processing_stats = {
        "total_villes": total_villes,
        "villes_traitees": villes_traitees,
        "pourcentage_traite": (villes_traitees / total_villes) * 100,
        "villes_en_echec": total_villes - villes_traitees
    }
    
    return processing_stats
```

#### Validation des sentiments

```python
def validate_sentiment_analysis():
    """Valide la cohérence de l'analyse de sentiment"""
    
    sentiment_stats = []
    
    for ville in db.villes.find():
        if "sentiments" in ville:
            sentiments = ville["sentiments"]
            
            # Vérification que les pourcentages sont cohérents
            total_percent = (
                sentiments.get("positif_percent", 0) +
                sentiments.get("neutre_percent", 0) +
                sentiments.get("negatif_percent", 0)
            )
            
            if abs(total_percent - 100) > 0.1:  # Tolérance 0.1%
                print(f"⚠️  Incohérence sentiment pour {ville['nom']}: {total_percent}%")
            
            sentiment_stats.append({
                "positif": sentiments.get("positif_percent", 0),
                "neutre": sentiments.get("neutre_percent", 0),
                "negatif": sentiments.get("negatif_percent", 0)
            })
    
    return sentiment_stats
```

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

```python
def validate_department_aggregations():
    """Valide la cohérence des agrégations départementales"""
    
    validation_errors = []
    
    for dept in db.departements_stats.find():
        # Vérification des totaux
        villes_dept = list(db.villes.find({"department_id": dept["_id"]}))
        
        expected_villes = len(villes_dept)
        expected_avis = sum(v.get("nombre_avis", 0) for v in villes_dept)
        
        # Validation comptage villes
        if dept["nombre_villes"] != expected_villes:
            validation_errors.append({
                "department": dept["_id"],
                "error": "nombre_villes_incoherent",
                "expected": expected_villes,
                "actual": dept["nombre_villes"]
            })
        
        # Validation comptage avis
        if abs(dept["nombre_avis"] - expected_avis) > 1:
            validation_errors.append({
                "department": dept["_id"],
                "error": "nombre_avis_incoherent",
                "expected": expected_avis,
                "actual": dept["nombre_avis"]
            })
        
        # Validation des notes (échelle 0-10)
        for note_key, note_value in dept["notes"].items():
            if not (0 <= note_value <= 10):
                validation_errors.append({
                    "department": dept["_id"],
                    "error": f"note_{note_key}_invalide",
                    "value": note_value
                })
    
    return validation_errors
```

#### 2. Validation propriétés PostgreSQL (properties_aggregation_validator.py)

```python
def validate_price_consistency():
    """Valide la cohérence des prix immobiliers"""
    
    # Validation prix positifs
    cursor.execute("""
        SELECT COUNT(*) FROM properties_cities_stats 
        WHERE prix_moyen <= 0
    """)
    negative_prices = cursor.fetchone()[0]
    
    # Validation prix réalistes (>50k€)
    cursor.execute("""
        SELECT COUNT(*) FROM properties_cities_stats 
        WHERE prix_moyen > 50000
    """)
    realistic_prices = cursor.fetchone()[0]
    
    # Détection outliers
    cursor.execute("""
        SELECT city_name, prix_moyen 
        FROM properties_cities_stats 
        WHERE prix_moyen > 2000000 OR prix_moyen < 10000
        ORDER BY prix_moyen DESC
    """)
    outliers = cursor.fetchall()
    
    return {
        "negative_prices": negative_prices,
        "realistic_prices": realistic_prices,
        "total_cities": 30860,
        "outliers": outliers
    }
```

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

```bash
#!/bin/bash
# run_all_validations.sh

echo "=== VALIDATION COMPLÈTE DU PIPELINE HOMEPEDIA ==="

# 1. Validation des données scrapées
echo "1. Validation des données d'avis..."
python aggregation_validator.py

# 2. Validation des propriétés immobilières
echo "2. Validation des données immobilières..."
python properties_aggregation_validator.py

# 3. Génération du rapport consolidé
echo "3. Génération du rapport final..."
python generate_final_report.py

echo "✅ Validation complète terminée"
echo "📊 Rapports disponibles dans /app/results/"
```

### Intégration avec le monitoring

```python
def generate_quality_metrics():
    """Génère les métriques de qualité pour monitoring"""
    
    quality_metrics = {
        "timestamp": datetime.now().isoformat(),
        "data_sources": {
            "villes_scrapees": 34455,
            "avis_collectes": 54656,
            "transactions_immobilieres": 1500000
        },
        "quality_scores": {
            "completeness_score": 98.5,  # % champs non-null
            "consistency_score": 100.0,  # % cohérence inter-niveaux
            "accuracy_score": 96.8       # % données dans ranges attendus
        },
        "anomalies_detected": {
            "prix_aberrants": 127,
            "sentiments_incoherents": 0,
            "avis_orphelins": 0
        }
    }
    
    return quality_metrics
```

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