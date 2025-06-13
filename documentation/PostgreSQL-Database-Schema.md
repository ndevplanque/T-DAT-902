# Documentation PostgreSQL - Base de Données Homepedia

## Vue d'ensemble

La base de données PostgreSQL du projet Homepedia stocke les données géographiques et immobilières de la France. Elle utilise l'extension PostGIS pour la gestion des données spatiales et comprend deux grandes catégories de données :

1. **Données géographiques** : Régions, départements et communes avec leurs contours géographiques
2. **Données immobilières** : Transactions DVF (Demandes de Valeurs Foncières) et leurs agrégations statistiques

## Architecture générale

### Extensions requises
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

L'extension PostGIS est essentielle pour :
- Stockage des géométries (points, polygones)
- Requêtes spatiales (intersection, distance, aire)
- Index spatiaux GIST pour les performances

## Schéma des données géographiques

### Table `regions`

**Objectif** : Stockage des 26 régions françaises avec leurs contours géographiques.

```sql
CREATE TABLE regions (
    region_id VARCHAR(10) PRIMARY KEY,    -- Code région INSEE (ex: "84")
    name TEXT NOT NULL,                   -- Nom officiel (ex: "Auvergne-Rhône-Alpes")
    geom GEOMETRY(MULTIPOLYGON, 4326)     -- Contour géographique en WGS84
);
```

**Choix de design** :
- `region_id` : Utilisation des codes INSEE officiels pour la cohérence
- `MULTIPOLYGON` : Une région peut contenir plusieurs territoires non contigus (îles, enclaves)
- `SRID 4326` : Système de coordonnées WGS84 standard, compatible avec les API web

**Index** :
```sql
CREATE INDEX idx_regions_geom ON regions USING GIST (geom);
```

### Table `departments`

**Objectif** : Stockage des 109 départements français avec liens hiérarchiques vers les régions.

```sql
CREATE TABLE departments (
    department_id VARCHAR(10) PRIMARY KEY,   -- Code département (ex: "01", "2A", "971")
    name TEXT NOT NULL,                      -- Nom officiel (ex: "Ain")
    region_id VARCHAR(10) NOT NULL,          -- FK vers regions
    geom GEOMETRY(MULTIPOLYGON, 4326),       -- Contour géographique
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE
);
```

**Choix de design** :
- `VARCHAR(10)` pour `department_id` : Support des codes spéciaux (2A/2B pour la Corse, DOM-TOM)
- `CASCADE` : Suppression automatique des départements si la région parent est supprimée
- Référence explicite `region_id` : Facilite les requêtes d'agrégation

**Index** :
```sql
CREATE INDEX idx_departments_geom ON departments USING GIST (geom);
```

### Table `cities`

**Objectif** : Stockage des 34 455 communes françaises avec double référencement (département et région).

```sql
CREATE TABLE cities (
    city_id VARCHAR(10) PRIMARY KEY,     -- Code commune INSEE (ex: "01001")
    name TEXT NOT NULL,                  -- Nom officiel
    department_id VARCHAR(10) NOT NULL,  -- FK vers departments
    region_id VARCHAR(10) NOT NULL,      -- FK vers regions (dénormalisé)
    geom GEOMETRY(MULTIPOLYGON, 4326),   -- Contour géographique
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE CASCADE,
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE
);
```

**Choix de design** :
- **Dénormalisation** de `region_id` : Évite les jointures systématiques cities→departments→regions
- Optimise les requêtes d'agrégation par région
- Trade-off : Espace disque vs performance des requêtes

**Index** :
```sql
CREATE INDEX idx_cities_geom ON cities USING GIST (geom);
```

## Schéma des données immobilières

### Table `properties`

**Objectif** : Stockage des transactions immobilières DVF (Demandes de Valeurs Foncières).

```sql
CREATE TABLE properties (
    id_mutation TEXT NOT NULL,              -- Identifiant unique de la transaction
    date_mutation DATE,                     -- Date de la vente
    valeur_fonciere DOUBLE PRECISION,       -- Prix de vente en euros
    code_postal TEXT,                       -- Code postal du bien
    code_commune TEXT,                      -- Code INSEE de la commune
    nom_commune TEXT,                       -- Nom de la commune
    id_parcelle TEXT NOT NULL,              -- Identifiant de la parcelle cadastrale
    surface_reelle_bati DOUBLE PRECISION,   -- Surface bâtie en m²
    surface_terrain DOUBLE PRECISION,       -- Surface du terrain en m²
    geom GEOMETRY(Point, 4326),             -- Localisation GPS du bien
    PRIMARY KEY (id_mutation, id_parcelle)  -- Clé composite
);
```

**Choix de design** :

#### Clé primaire composite
- `(id_mutation, id_parcelle)` : Une mutation peut concerner plusieurs parcelles
- Évite les doublons lors des imports en lot

#### Types de données
- `DOUBLE PRECISION` pour les prix/surfaces : Précision nécessaire pour les calculs financiers
- `Point` geometry : Position exacte du bien (vs polygon pour la parcelle complète)
- `TEXT` pour les codes : Flexibilité face aux évolutions des nomenclatures INSEE

#### Champs conservés vs écartés
**Conservés** :
- `valeur_fonciere` : Essentiel pour les analyses de prix
- `surface_*` : Calculs de prix au m²
- `code_commune` : Liaison avec les données géographiques
- `geom` : Analyses spatiales

**Écartés** (présents dans DVF brut) :
- `type_local` : Non utilisé dans les agrégations actuelles
- `nombre_pieces_principales` : Hors scope du projet
- `code_nature_culture` : Spécifique aux terrains agricoles

**Index** :
```sql
CREATE INDEX idx_properties_code_commune ON properties(code_commune);  -- Jointures fréquentes
CREATE INDEX idx_properties_date_mutation ON properties(date_mutation);  -- Filtres temporels
CREATE INDEX idx_properties_geom ON properties USING GIST (geom);        -- Requêtes spatiales
```

## Schéma des agrégations immobilières

### Vue d'ensemble des tables d'agrégation

Le système d'agrégation calcule des statistiques immobilières à trois niveaux :
1. `properties_cities_stats` : Par ville
2. `properties_departments_stats` : Par département 
3. `properties_regions_stats` : Par région

### Table `properties_cities_stats`

**Objectif** : Statistiques immobilières précalculées par ville.

```sql
CREATE TABLE properties_cities_stats (
    city_id VARCHAR(10) PRIMARY KEY,
    city_name TEXT NOT NULL,
    department_id VARCHAR(10) NOT NULL,
    region_id VARCHAR(10) NOT NULL,
    
    -- Compteurs de transactions
    nb_transactions INTEGER DEFAULT 0,
    nb_transactions_with_surface_bati INTEGER DEFAULT 0,
    nb_transactions_with_surface_terrain INTEGER DEFAULT 0,
    
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
    
    -- Analyse temporelle
    premiere_transaction DATE,
    derniere_transaction DATE,
    
    -- Densité géographique
    densite_transactions_km2 DOUBLE PRECISION,
    
    -- Métadonnées
    date_extraction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Justifications techniques** :

#### Précalcul vs calcul à la volée
- **Avantage** : Réponse instantanée pour l'API frontend
- **Inconvénient** : Espace disque supplémentaire
- **Décision** : Précalcul choisi pour les performances UX

#### Métriques statistiques
- **Moyennes ET médianes** : Robustesse face aux valeurs aberrantes immobilières
- **Min/Max** : Détection d'anomalies dans les données
- **Densité spatiale** : Indicateur d'activité immobilière locale

#### Métadonnées temporelles
- `date_extraction` : Traçabilité des mises à jour d'agrégation
- `premiere_transaction` / `derniere_transaction` : Période d'activité de la ville

### Tables `properties_departments_stats` et `properties_regions_stats`

**Structure similaire** avec agrégation hiérarchique :

```sql
-- Départements : agrégation des statistiques des villes
nb_villes_avec_transactions INTEGER DEFAULT 0,
nb_transactions_total INTEGER DEFAULT 0,

-- Régions : agrégation des statistiques des départements  
nb_departements_avec_transactions INTEGER DEFAULT 0,
nb_villes_avec_transactions INTEGER DEFAULT 0,
```

**Méthodes d'agrégation** :
- **Sommes** : `nb_transactions`, `nb_villes`
- **Moyennes pondérées** : `prix_moyen` pondéré par `nb_transactions`
- **Médianes de médianes** : `prix_median` via `PERCENTILE_CONT`
- **Min/Max globaux** : Extremums sur l'ensemble du territoire

## Stratégie d'indexation

### Index spatiaux (GIST)
```sql
-- Obligatoires pour les performances PostGIS
CREATE INDEX idx_regions_geom ON regions USING GIST (geom);
CREATE INDEX idx_departments_geom ON departments USING GIST (geom);
CREATE INDEX idx_cities_geom ON cities USING GIST (geom);
CREATE INDEX idx_properties_geom ON properties USING GIST (geom);
```

### Index métier
```sql
-- Jointures fréquentes entre properties et cities
CREATE INDEX idx_properties_code_commune ON properties(code_commune);

-- Filtres temporels sur les transactions
CREATE INDEX idx_properties_date_mutation ON properties(date_mutation);

-- Recherches et tris par prix dans l'API
CREATE INDEX idx_properties_cities_stats_prix_moyen ON properties_cities_stats(prix_moyen);
CREATE INDEX idx_properties_departments_stats_prix_moyen ON properties_departments_stats(prix_moyen);
CREATE INDEX idx_properties_regions_stats_prix_moyen ON properties_regions_stats(prix_moyen);

-- Recherches par volume de transactions
CREATE INDEX idx_properties_cities_stats_nb_transactions ON properties_cities_stats(nb_transactions);
CREATE INDEX idx_properties_departments_stats_nb_transactions ON properties_departments_stats(nb_transactions_total);
CREATE INDEX idx_properties_regions_stats_nb_transactions ON properties_regions_stats(nb_transactions_total);
```

## Contraintes d'intégrité

### Clés étrangères avec CASCADE
```sql
-- Suppression en cascade : région → départements → villes
FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE
FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE CASCADE

-- Cohérence dans les agrégations
FOREIGN KEY (city_id) REFERENCES cities(city_id) ON DELETE CASCADE
```

### Contraintes métier
- **NOT NULL** sur les noms et identifiants : Données essentielles
- **DEFAULT 0** sur les compteurs : Évite les valeurs NULL dans les agrégations
- **CURRENT_TIMESTAMP** : Traçabilité automatique des extractions

## Volumétrie et performances

### Données de référence
- **Régions** : 26 enregistrements (~10 KB)
- **Départements** : 109 enregistrements (~50 KB)  
- **Villes** : 34 455 enregistrements (~15 MB avec géométries)
- **Properties** : Variable selon les données DVF importées

### Optimisations spatiales
- **Simplification géométrique** : Contours simplifiés à 1000m pour les performances web
- **SRID uniforme** : WGS84 (4326) pour éviter les conversions
- **Index GIST** : Recherches spatiales en temps logarithmique

### Stratégie de partitionnement (future)
Pour les très gros volumes de transactions :
```sql
-- Partitionnement par année pour les properties
CREATE TABLE properties_2023 PARTITION OF properties 
FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
```

## Scripts de maintenance

### Nettoyage des géométries
```sql
-- Validation et réparation des géométries invalides
UPDATE regions SET geom = ST_MakeValid(geom) WHERE NOT ST_IsValid(geom);
UPDATE departments SET geom = ST_MakeValid(geom) WHERE NOT ST_IsValid(geom);
UPDATE cities SET geom = ST_MakeValid(geom) WHERE NOT ST_IsValid(geom);
```

### Recalcul des agrégations
```sql
-- Rafraîchissement complet des statistiques
TRUNCATE properties_cities_stats, properties_departments_stats, properties_regions_stats CASCADE;
-- Puis relancer le processus d'agrégation via data-aggregator
```

### Analyse des performances
```sql
-- Statistiques des index
SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch 
FROM pg_stat_user_indexes 
WHERE schemaname = 'public';

-- Requêtes lentes
SELECT query, mean_time, calls 
FROM pg_stat_statements 
WHERE query LIKE '%properties%' 
ORDER BY mean_time DESC;
```

## Connexions externes

### Liaison avec MongoDB
- **Code commune** : Clé de liaison entre `properties.code_commune` et `villes.city_id` (MongoDB)
- **Pas de contraintes FK** : Bases indépendantes pour la flexibilité

### API Backend  
- **Endpoints spatiaux** : Utilisation intensive des index GIST
- **Cache des agrégations** : Tables précalculées pour éviter les calculs à la volée
- **Format GeoJSON** : Conversion automatique via `ST_AsGeoJSON()`

## Sécurité et accès

### Utilisateurs et rôles
```sql
-- Utilisateur applicatif (lecture/écriture limitée)
CREATE USER homepedia_app WITH PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO homepedia_app;

-- Utilisateur ETL (pour les imports)  
CREATE USER homepedia_etl WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO homepedia_etl;
```

### Sauvegarde et restauration
```bash
# Sauvegarde complète
pg_dump -h postgres -U postgres -d gis_db > backup_$(date +%Y%m%d).sql

# Sauvegarde des données uniquement (sans schéma)
pg_dump -h postgres -U postgres -d gis_db --data-only > data_backup.sql

# Restauration
psql -h postgres -U postgres -d gis_db < backup.sql
```

Cette architecture PostgreSQL garantit :
- **Performance** : Index optimisés pour les requêtes spatiales et métier
- **Cohérence** : Contraintes d'intégrité référentielle
- **Scalabilité** : Structure préparée pour le partitionnement
- **Maintenabilité** : Documentation des choix techniques et scripts de maintenance