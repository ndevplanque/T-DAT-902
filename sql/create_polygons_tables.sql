-- Activer l'extension PostGIS si ce n'est pas déjà fait
CREATE EXTENSION IF NOT EXISTS postgis;

-- --------------------------
-- TABLE REGIONS
-- --------------------------
CREATE TABLE regions (
    region_id VARCHAR(10) PRIMARY KEY,    -- Code région (ex: "84")
    name TEXT NOT NULL,                   -- Nom de la région (ex: "Auvergne-Rhône-Alpes")
    geom GEOMETRY(MULTIPOLYGON, 4326)     -- Contour géographique de la région
);

-- Ajouter un index spatial pour optimiser les requêtes PostGIS
CREATE INDEX idx_regions_geom ON regions USING GIST (geom);

-- --------------------------
-- TABLE DEPARTMENTS
-- --------------------------
CREATE TABLE departments (
    department_id VARCHAR(10) PRIMARY KEY,   -- Code département (ex: "01" pour Ain)
    name TEXT NOT NULL,                      -- Nom du département (ex: "Ain")
    region_id VARCHAR(10) NOT NULL,          -- Clé étrangère vers regions (ex: "84" pour Auvergne-Rhône-Alpes)
    geom GEOMETRY(MULTIPOLYGON, 4326),       -- Contour géographique du département
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE
);

-- Ajouter un index spatial pour optimiser les requêtes spatiales
CREATE INDEX idx_departments_geom ON departments USING GIST (geom);

-- --------------------------
-- TABLE CITIES
-- --------------------------
CREATE TABLE cities (
    city_id VARCHAR(10) PRIMARY KEY,     -- Code commune (ex: "01001" pour L'Abergement-Clémenciat)
    name TEXT NOT NULL,                  -- Nom de la commune
    department_id VARCHAR(10) NOT NULL,  -- Clé étrangère vers departments (ex: "01" pour Ain)
    region_id VARCHAR(10) NOT NULL,      -- Clé étrangère vers regions (ex: "84" pour Auvergne-Rhône-Alpes)
    geom GEOMETRY(MULTIPOLYGON, 4326),        -- Contour géographique de la commune
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE CASCADE,
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE
);

-- Ajouter un index spatial pour optimiser les requêtes spatiales
CREATE INDEX idx_cities_geom ON cities USING GIST (geom);