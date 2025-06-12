# Data Aggregator - Service d'agrégation et consolidation

## Vue d'ensemble

Le service **data-aggregator** constitue le cœur analytique de Homepedia, responsable de l'agrégation et de la consolidation des données à différents niveaux géographiques. Il orchestre la transformation des données brutes (avis par ville, transactions immobilières) en statistiques structurées prêtes pour l'API et le dashboard, en gérant deux flux de données parallèles depuis MongoDB et PostgreSQL.

## Architecture du service

### Responsabilités principales

1. **Agrégation géographique**: Calcul des statistiques par département et région
2. **Consolidation multi-sources**: Fusion données d'avis (MongoDB) et immobilières (PostgreSQL)
3. **Calculs statistiques**: Moyennes pondérées, médianes, percentiles
4. **Validation croisée**: Contrôle de cohérence entre niveaux d'agrégation
5. **Optimisation API**: Création de tables/collections optimisées pour les requêtes

### Position dans le pipeline

```
Pipeline Data Aggregator
├── Input Sources
│   ├── MongoDB: villes, avis, mots_villes
│   └── PostgreSQL: cities, properties
├── Processing Engine
│   ├── Agrégation départementale
│   ├── Agrégation régionale  
│   └── Calculs statistiques pondérés
└── Output Collections/Tables
    ├── MongoDB: departements_stats, regions_stats
    └── PostgreSQL: properties_*_stats
```

## Configuration Docker

### Service principal

```yaml
data-aggregator:
  build:
    context: ./data-aggregator
    dockerfile: Dockerfile
  container_name: data-aggregator
  restart: on-failure
  environment:
    - MONGO_URI=mongodb://root:rootpassword@mongodb:27017/
    - MONGO_DB=villes_france
    - POSTGRES_DB=gis_db
    - POSTGRES_USER=postgres
    - POSTGRES_PASSWORD=postgres
    - POSTGRES_HOST=postgres
    - POSTGRES_PORT=5432
  depends_on:
    - mongodb
    - postgres
    - avis-scraper
    - avis-processor-submitter
    - avis-processor-validator
    - geo-data-importer
    - properties-importer
```

### Dépendances critiques

Le data-aggregator s'exécute en dernier dans la chaîne, nécessitant:
1. **Données géographiques** complètes (geo-data-importer)
2. **Données d'avis** traitées (avis-processor)
3. **Données immobilières** importées (properties-importer)
4. **Mapping départements→régions** depuis PostgreSQL

## Processus d'agrégation MongoDB

### Sources de données

**Collections sources**:
- `villes`: 34,455 villes avec notes et sentiments
- `avis`: 54,656 avis individuels
- `mots_villes`: Fréquences mots par ville

### Pipeline d'agrégation départementale

```javascript
// Script aggregation.py - Logique MongoDB
db.villes.aggregate([
    {
        $group: {
            _id: "$department_id",
            nombre_villes: { $sum: 1 },
            nombre_avis: { $sum: "$nombre_avis" },
            
            // Moyennes pondérées par nombre d'avis
            moyenne_globale: {
                $sum: { $multiply: ["$notes.moyenne", "$nombre_avis"] }
            },
            poids_total: { $sum: "$nombre_avis" },
            
            // Agrégation des sentiments
            sentiments_positifs: { $sum: "$sentiments.positif" },
            sentiments_neutres: { $sum: "$sentiments.neutre" },
            sentiments_negatifs: { $sum: "$sentiments.negatif" }
        }
    },
    {
        $project: {
            _id: 1,
            nombre_villes: 1,
            nombre_avis: 1,
            moyenne_globale: {
                $divide: ["$moyenne_globale", "$poids_total"]
            },
            sentiments: {
                positif: "$sentiments_positifs",
                neutre: "$sentiments_neutres", 
                negatif: "$sentiments_negatifs",
                positif_percent: {
                    $multiply: [
                        { $divide: ["$sentiments_positifs", "$nombre_avis"] },
                        100
                    ]
                }
            }
        }
    }
])
```

### Agrégation des mots-clés

```python
def aggregate_words_by_department(department_id, villes_in_dept):
    """Agrège les mots-clés par département avec pondération"""
    
    word_aggregation = {}
    
    for ville in villes_in_dept:
        mots_ville = db.mots_villes.find_one({"city_id": ville["_id"]})
        
        if mots_ville and "mots" in mots_ville:
            for mot_info in mots_ville["mots"][:50]:  # Top 50 par ville
                mot = mot_info["mot"]
                poids = mot_info["poids"]
                
                if mot in word_aggregation:
                    word_aggregation[mot] += poids
                else:
                    word_aggregation[mot] = poids
    
    # Tri et limitation aux top 50 départementaux
    top_words = sorted(word_aggregation.items(), 
                      key=lambda x: x[1], reverse=True)[:50]
    
    return [{"mot": mot, "poids": poids} for mot, poids in top_words]
```

## Processus d'agrégation PostgreSQL

### Agrégation des données immobilières

#### Niveau département

```sql
-- Script create_properties_aggregations_tables.sql
INSERT INTO properties_departments_stats 
SELECT 
    d.department_id,
    d.name as department_name,
    d.region_id,
    
    -- Statistiques de base
    SUM(pcs.nb_transactions) as nb_transactions,
    COUNT(pcs.city_id) as nb_cities_with_data,
    
    -- Prix moyens pondérés par nombre de transactions
    SUM(pcs.prix_moyen * pcs.nb_transactions) / 
        NULLIF(SUM(pcs.nb_transactions), 0) as prix_moyen,
    
    -- Médiane départementale
    percentile_cont(0.5) WITHIN GROUP (
        ORDER BY pcs.prix_median
    ) as prix_median,
    
    -- Extremums
    MIN(pcs.prix_min) as prix_min,
    MAX(pcs.prix_max) as prix_max,
    
    -- Surfaces moyennes pondérées
    SUM(pcs.surface_bati_moyenne * pcs.nb_transactions_with_surface_bati) / 
        NULLIF(SUM(pcs.nb_transactions_with_surface_bati), 0) as surface_bati_moyenne,
    
    -- Densité (transactions/km²)
    SUM(pcs.nb_transactions) / ST_Area(ST_Union(c.geom)::geography) * 1000000 as densite_transactions_km2,
    
    -- Période d'activité
    MIN(pcs.premiere_transaction) as premiere_transaction,
    MAX(pcs.derniere_transaction) as derniere_transaction

FROM departments d
LEFT JOIN cities c ON c.department_id = d.department_id  
LEFT JOIN properties_cities_stats pcs ON pcs.city_id = c.city_id
WHERE pcs.nb_transactions > 0
GROUP BY d.department_id, d.name, d.region_id;
```

#### Niveau région

```sql
-- Agrégation région avec validation croisée
INSERT INTO properties_regions_stats
SELECT 
    r.region_id,
    r.name as region_name,
    
    SUM(pds.nb_transactions) as nb_transactions,
    COUNT(pds.department_id) as nb_departments_with_data,
    
    -- Prix moyen régional (pondéré par départements)
    SUM(pds.prix_moyen * pds.nb_transactions) / 
        NULLIF(SUM(pds.nb_transactions), 0) as prix_moyen,
    
    -- Validation: cohérence avec somme directe des villes
    (SELECT SUM(prix_moyen * nb_transactions) / SUM(nb_transactions)
     FROM properties_cities_stats pcs
     JOIN cities c ON c.city_id = pcs.city_id  
     WHERE c.region_id = r.region_id) as prix_moyen_validation

FROM regions r
LEFT JOIN properties_departments_stats pds ON pds.region_id = r.region_id
WHERE pds.nb_transactions > 0  
GROUP BY r.region_id, r.name;
```

## Schémas des données agrégées

### Collections MongoDB

#### departements_stats

```javascript
{
  _id: "01",                           // Code département
  nom: "Ain",
  region_id: "84",
  nombre_villes: 393,
  nombre_avis: 1247,
  notes: {
    moyenne: 3.2,
    securite: 3.1,
    education: 3.4,
    sport_loisir: 3.0,
    environnement: 3.5,
    vie_pratique: 3.1
  },
  sentiments: {
    positif: 450,
    neutre: 623,
    negatif: 174,
    positif_percent: 36.1,
    neutre_percent: 49.9,
    negatif_percent: 14.0
  },
  mots: [
    {mot: "ville", poids: 156.7},
    {mot: "commerce", poids: 89.3},
    // ... top 50 mots
  ],
  date_extraction: ISODate("2025-01-06")
}
```

#### regions_stats

Structure similaire avec agrégation de tous les départements.

### Tables PostgreSQL

#### properties_cities_stats (30,860 villes)

```sql
CREATE TABLE properties_cities_stats (
    city_id VARCHAR(10) PRIMARY KEY,
    city_name TEXT,
    department_id VARCHAR(10),
    region_id VARCHAR(10),
    
    -- Compteurs de transactions
    nb_transactions INTEGER NOT NULL,
    nb_transactions_with_surface_bati INTEGER,
    nb_transactions_with_surface_terrain INTEGER,
    
    -- Statistiques de prix
    prix_moyen DOUBLE PRECISION,
    prix_median DOUBLE PRECISION,
    prix_min DOUBLE PRECISION,
    prix_max DOUBLE PRECISION,
    prix_m2_moyen DOUBLE PRECISION,
    prix_m2_median DOUBLE PRECISION,
    
    -- Statistiques de surfaces
    surface_bati_moyenne DOUBLE PRECISION,
    surface_bati_mediane DOUBLE PRECISION,
    surface_terrain_moyenne DOUBLE PRECISION,
    surface_terrain_mediane DOUBLE PRECISION,
    
    -- Métadonnées temporelles
    premiere_transaction DATE,
    derniere_transaction DATE,
    
    -- Métrique géographique
    densite_transactions_km2 DOUBLE PRECISION,
    
    -- Contraintes d'intégrité
    FOREIGN KEY (city_id) REFERENCES cities(city_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (region_id) REFERENCES regions(region_id)
);
```

## Métriques et KPIs calculés

### Dashboard des avis (MongoDB)

**Statistiques globales**:
- **94 départements** avec données d'avis
- **12 régions** représentées
- **54,656 avis** agrégés
- **Note moyenne nationale**: 3.2/5

**Répartition des sentiments**:
- Positif: 34.7% (18,964 avis)
- Neutre: 50.3% (27,492 avis)  
- Négatif: 15.0% (8,200 avis)

**Top départements par note**:
1. Hautes-Alpes (05): 3.7/5
2. Ille-et-Vilaine (35): 3.7/5
3. Morbihan (56): 3.6/5

**Mots-clés principaux**:
1. "ville" (poids: 2,847)
2. "commerce" (poids: 1,634)
3. "bon" (poids: 1,523)
4. "petit" (poids: 1,456)
5. "agréable" (poids: 1,234)

### Dashboard immobilier (PostgreSQL)

**Statistiques globales**:
- **30,860 villes** avec transactions
- **Prix moyen national**: 150,681€
- **1,5M transactions** analysées
- **97 départements** couverts

**Top villes par volume**:
1. Nice: 4,604 transactions (354k€ moyen)
2. Toulouse: 4,430 transactions (291k€ moyen)
3. Nantes: 2,672 transactions (294k€ moyen)

**Extremums de prix**:
- Plus cher: Paris 15e à 24,271€/m²
- Moins cher: Saint-Étienne à 1,891€/m²
- Amplitude: ~13x de différence

## Validation et contrôle qualité

### Scripts de validation automatisée

#### 1. Validation MongoDB (aggregation_validator.py)

```python
def validate_department_aggregations():
    """Valide la cohérence des agrégations départementales"""
    
    errors = []
    
    for dept in db.departements_stats.find():
        # Validation des totaux
        villes_dept = list(db.villes.find({"department_id": dept["_id"]}))
        expected_cities = len(villes_dept)
        expected_avis = sum(v.get("nombre_avis", 0) for v in villes_dept)
        
        if dept["nombre_villes"] != expected_cities:
            errors.append(f"Département {dept['_id']}: nombre villes incohérent")
        
        if abs(dept["nombre_avis"] - expected_avis) > 1:
            errors.append(f"Département {dept['_id']}: nombre avis incohérent")
        
        # Validation des notes (0-10)
        for note_key, note_value in dept["notes"].items():
            if not (0 <= note_value <= 10):
                errors.append(f"Note {note_key} invalide: {note_value}")
        
        # Validation des pourcentages (somme = 100%)
        total_percent = (dept["sentiments"]["positif_percent"] + 
                        dept["sentiments"]["neutre_percent"] + 
                        dept["sentiments"]["negatif_percent"])
        
        if abs(total_percent - 100) > 0.1:
            errors.append(f"Pourcentages sentiments != 100%: {total_percent}")
    
    return errors
```

#### 2. Validation PostgreSQL (properties_aggregation_validator.py)

```python
def validate_price_consistency():
    """Valide la cohérence des prix entre niveaux"""
    
    # Validation prix > 50k€ (seuil de cohérence)
    valid_cities = cursor.execute("""
        SELECT COUNT(*) FROM properties_cities_stats 
        WHERE prix_moyen > 50000
    """).fetchone()[0]
    
    print(f"Villes avec prix > 50k€: {valid_cities}/30,860")
    
    # Détection prix aberrants
    outliers = cursor.execute("""
        SELECT city_name, prix_moyen 
        FROM properties_cities_stats 
        WHERE prix_moyen > 2000000 OR prix_moyen < 10000
        ORDER BY prix_moyen DESC
    """).fetchall()
    
    if outliers:
        print(f"⚠️  {len(outliers)} prix aberrants détectés")
        for city, price in outliers[:10]:
            print(f"  {city}: {price:,.0f}€")
```

### Outputs de validation

**Génération automatique**:
- Rapports HTML avec graphiques
- Exports JSON des métriques clés
- Logs détaillés par étape
- Visualisations (distributions, heatmaps)

**Métriques de qualité**:
- 0 incohérence entre niveaux d'agrégation
- 100% de cohérence géographique département→région
- 22,800/30,860 villes (74%) avec prix > 50k€ (seuil réaliste)

## Performance et optimisations

### Optimisations MongoDB

1. **Bulk operations**: Upserts groupés pour performance
2. **Index composites**: Sur department_id, region_id
3. **Pipeline optimization**: Agrégations en une seule passe
4. **Memory management**: Traitement par batches

### Optimisations PostgreSQL

1. **CTE complexes**: Calculs en une passe SQL
2. **Index spatiaux**: GIST sur géométries pour densité
3. **Moyennes pondérées**: Évite les biais de petites villes
4. **Transactions**: Atomicité des agrégations

### Métriques de performance

- **Temps d'exécution**: ~5-10 minutes total
- **Données traitées**: 34k villes + 1.5M transactions
- **Mémoire utilisée**: <2GB peak
- **Parallélisme**: Agrégations MongoDB et PostgreSQL en parallèle

Le service data-aggregator transforme efficacement les données brutes en insights structurés, constituant le fondement analytique de l'écosystème Homepedia avec des garanties de qualité et de cohérence.