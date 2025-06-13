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

Ce pipeline d'agrégation MongoDB regroupe les données de la collection `villes` par département. Pour chaque département, il calcule :

- Le nombre total de villes.
- Le nombre total d'avis.
- La moyenne globale des notes, pondérée par le nombre d'avis de chaque ville.
- Le total des avis positifs, neutres et négatifs.

Ensuite, il projette pour chaque département :

- L’identifiant du département.
- Le nombre de villes et d’avis.
- La moyenne globale calculée.
- Un objet `sentiments` contenant :
  - Le nombre d’avis positifs, neutres et négatifs.
  - Le pourcentage d’avis positifs par rapport au total d’avis.

### Agrégation des mots-clés

La fonction décrite agrège les mots-clés par département avec un système de pondération. Voici son fonctionnement :

1. Elle prend en entrée l'identifiant d'un département et la liste des villes appartenant à ce département.
2. Pour chaque ville, elle récupère ses mots-clés depuis la collection MongoDB `mots_villes`.
3. Elle traite uniquement les 50 mots les plus importants par ville.
4. Elle accumule le poids de chaque mot au niveau départemental, additionnant les occurrences à travers toutes les villes.
5. Si un mot apparaît dans plusieurs villes, son poids total augmente proportionnellement.
6. Finalement, elle trie tous les mots par poids décroissant et conserve uniquement les 50 mots les plus significatifs du département.
7. Le résultat est une liste formatée où chaque entrée contient un mot et son poids agrégé.

Ce processus permet d'identifier les termes les plus représentatifs pour chaque département, reflétant les caractéristiques et thèmes récurrents mentionnés dans les avis des villes composant ce département.

## Processus d'agrégation PostgreSQL

### Agrégation des données immobilières

#### Niveau département

Le code SQL associé à ce niveau effectue une agrégation des données immobilières par département, en produisant un ensemble de statistiques consolidées. Voici une explication simplifiée :  
Le script insère dans la table properties_departments_stats des statistiques regroupées pour chaque département.

Pour chaque département, il calcule :

- Des informations d'identification (ID, nom, région)
- Le nombre total de transactions immobilières
- Le nombre de villes ayant des données dans le département
- Un prix moyen pondéré par le nombre de transactions
- Un prix médian départemental
- Les prix minimum et maximum enregistrés
- La surface bâtie moyenne pondérée
- La densité de transactions par km²
- Les dates de première et dernière transaction

Ces calculs sont réalisés en joignant trois tables :  
- departments : contient les informations sur les départements
- cities : contient les informations sur les villes
- properties_cities_stats : contient les statistiques immobilières par ville

Seuls les départements ayant au moins une transaction sont inclus (clause WHERE).  
Les résultats sont groupés par département pour obtenir une ligne de statistiques par département.  
Cette agrégation transforme des données détaillées au niveau des villes en une vue synthétique du marché immobilier à l'échelle départementale.

#### Niveau région

Ce code SQL effectue une agrégation des statistiques immobilières au niveau régional en calculant le prix moyen pondéré et
le nombre de transactions par région, tout en incluant une validation croisée pour vérifier la cohérence des calculs
par rapport aux données sources des villes.

Ce code génère à peu près les mêmes données que le niveau départemental, mais au niveau régional.

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

Valide la cohérence des agrégations départementales en vérifiant:
- Correspondance entre le nombre de villes agrégées et les villes sources
- Cohérence du nombre total d'avis par département
- Validité des notes sur l'échelle 0-10
- Cohérence des pourcentages de sentiments (somme = 100%)

#### 2. Validation PostgreSQL (properties_aggregation_validator.py)

Contrôle la qualité des données immobilières agrégées:
- Détection des prix aberrants (< 10k€ ou > 2M€)
- Validation du seuil de cohérence (prix > 50k€)
- Vérification de la distribution des prix entre niveaux géographiques

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