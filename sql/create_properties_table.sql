CREATE TABLE IF NOT EXISTS properties (
    id_mutation TEXT NOT NULL,
    date_mutation DATE,
    valeur_fonciere DOUBLE PRECISION,
    code_postal TEXT,
    code_commune TEXT,
    nom_commune TEXT,
    id_parcelle TEXT NOT NULL,
    surface_reelle_bati DOUBLE PRECISION,
    surface_terrain DOUBLE PRECISION,
    geom geometry(Point, 4326),
    PRIMARY KEY (id_mutation, id_parcelle)
);

-- Index classiques
CREATE INDEX idx_properties_code_commune ON properties(code_commune);
CREATE INDEX idx_properties_id_parcelle ON properties(id_parcelle);
CREATE INDEX idx_properties_date_mutation ON properties(date_mutation);

-- ✅ Index spatial
CREATE INDEX idx_properties_geom ON properties USING GIST (geom);