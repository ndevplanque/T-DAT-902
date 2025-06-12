-- Tables d'agrégation pour les données immobilières

-- ============================================
-- Table des statistiques par ville
-- ============================================
CREATE TABLE IF NOT EXISTS properties_cities_stats (
    city_id VARCHAR(10) PRIMARY KEY,
    city_name TEXT NOT NULL,
    department_id VARCHAR(10) NOT NULL,
    region_id VARCHAR(10) NOT NULL,
    
    -- Compteurs
    nb_transactions INTEGER DEFAULT 0,
    nb_transactions_with_surface_bati INTEGER DEFAULT 0,
    nb_transactions_with_surface_terrain INTEGER DEFAULT 0,
    
    -- Prix
    prix_moyen DOUBLE PRECISION,
    prix_median DOUBLE PRECISION,
    prix_min DOUBLE PRECISION,
    prix_max DOUBLE PRECISION,
    prix_m2_moyen DOUBLE PRECISION,
    prix_m2_median DOUBLE PRECISION,
    
    -- Surfaces
    surface_bati_moyenne DOUBLE PRECISION,
    surface_bati_mediane DOUBLE PRECISION,
    surface_terrain_moyenne DOUBLE PRECISION,
    surface_terrain_mediane DOUBLE PRECISION,
    
    -- Périodes temporelles
    premiere_transaction DATE,
    derniere_transaction DATE,
    
    -- Densité
    densite_transactions_km2 DOUBLE PRECISION,
    
    -- Métadonnées
    date_extraction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (city_id) REFERENCES cities(city_id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE CASCADE,
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE
);

-- ============================================
-- Table des statistiques par département
-- ============================================
CREATE TABLE IF NOT EXISTS properties_departments_stats (
    department_id VARCHAR(10) PRIMARY KEY,
    department_name TEXT NOT NULL,
    region_id VARCHAR(10) NOT NULL,
    
    -- Compteurs agrégés
    nb_villes_avec_transactions INTEGER DEFAULT 0,
    nb_transactions_total INTEGER DEFAULT 0,
    nb_transactions_with_surface_bati INTEGER DEFAULT 0,
    nb_transactions_with_surface_terrain INTEGER DEFAULT 0,
    
    -- Prix agrégés (moyennes pondérées)
    prix_moyen DOUBLE PRECISION,
    prix_median DOUBLE PRECISION,
    prix_min DOUBLE PRECISION,
    prix_max DOUBLE PRECISION,
    prix_m2_moyen DOUBLE PRECISION,
    prix_m2_median DOUBLE PRECISION,
    
    -- Surfaces agrégées
    surface_bati_moyenne DOUBLE PRECISION,
    surface_bati_mediane DOUBLE PRECISION,
    surface_terrain_moyenne DOUBLE PRECISION,
    surface_terrain_mediane DOUBLE PRECISION,
    
    -- Périodes temporelles
    premiere_transaction DATE,
    derniere_transaction DATE,
    
    -- Densité agrégée
    densite_transactions_km2 DOUBLE PRECISION,
    
    -- Métadonnées
    date_extraction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE CASCADE,
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE
);

-- ============================================
-- Table des statistiques par région
-- ============================================
CREATE TABLE IF NOT EXISTS properties_regions_stats (
    region_id VARCHAR(10) PRIMARY KEY,
    region_name TEXT NOT NULL,
    
    -- Compteurs agrégés
    nb_departements_avec_transactions INTEGER DEFAULT 0,
    nb_villes_avec_transactions INTEGER DEFAULT 0,
    nb_transactions_total INTEGER DEFAULT 0,
    nb_transactions_with_surface_bati INTEGER DEFAULT 0,
    nb_transactions_with_surface_terrain INTEGER DEFAULT 0,
    
    -- Prix agrégés (moyennes pondérées)
    prix_moyen DOUBLE PRECISION,
    prix_median DOUBLE PRECISION,
    prix_min DOUBLE PRECISION,
    prix_max DOUBLE PRECISION,
    prix_m2_moyen DOUBLE PRECISION,
    prix_m2_median DOUBLE PRECISION,
    
    -- Surfaces agrégées
    surface_bati_moyenne DOUBLE PRECISION,
    surface_bati_mediane DOUBLE PRECISION,
    surface_terrain_moyenne DOUBLE PRECISION,
    surface_terrain_mediane DOUBLE PRECISION,
    
    -- Périodes temporelles
    premiere_transaction DATE,
    derniere_transaction DATE,
    
    -- Densité agrégée
    densite_transactions_km2 DOUBLE PRECISION,
    
    -- Métadonnées
    date_extraction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE
);

-- ============================================
-- Index pour optimiser les performances
-- ============================================

-- Index pour les villes
CREATE INDEX IF NOT EXISTS idx_properties_cities_stats_department ON properties_cities_stats(department_id);
CREATE INDEX IF NOT EXISTS idx_properties_cities_stats_region ON properties_cities_stats(region_id);
CREATE INDEX IF NOT EXISTS idx_properties_cities_stats_prix_moyen ON properties_cities_stats(prix_moyen);
CREATE INDEX IF NOT EXISTS idx_properties_cities_stats_nb_transactions ON properties_cities_stats(nb_transactions);

-- Index pour les départements
CREATE INDEX IF NOT EXISTS idx_properties_departments_stats_region ON properties_departments_stats(region_id);
CREATE INDEX IF NOT EXISTS idx_properties_departments_stats_prix_moyen ON properties_departments_stats(prix_moyen);
CREATE INDEX IF NOT EXISTS idx_properties_departments_stats_nb_transactions ON properties_departments_stats(nb_transactions_total);

-- Index pour les régions
CREATE INDEX IF NOT EXISTS idx_properties_regions_stats_prix_moyen ON properties_regions_stats(prix_moyen);
CREATE INDEX IF NOT EXISTS idx_properties_regions_stats_nb_transactions ON properties_regions_stats(nb_transactions_total);