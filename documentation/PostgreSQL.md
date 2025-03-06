# **Documentation DB PostgreSQL**

## **1. Tables Géographiques**

### **Table `regions`**
Stocke les informations sur les régions administratives de France.

| Champ        | Type                        | Description |
|-------------|----------------------------|-------------|
| region_id   | VARCHAR(10)  (PK)           | Code unique de la région (ex. "84") |
| name        | TEXT NOT NULL               | Nom de la région (ex. "Auvergne-Rhône-Alpes") |
| geom        | GEOMETRY(MULTIPOLYGON, 4326) | Contour géographique de la région |

*Index spatial :*
```sql
CREATE INDEX idx_regions_geom ON regions USING GIST (geom);
```

---

### **Table `departments`**
Stocke les informations sur les départements administratifs de France.

| Champ          | Type                        | Description |
|---------------|----------------------------|-------------|
| department_id | VARCHAR(10)  (PK)           | Code unique du département (ex. "01" pour Ain) |
| name          | TEXT NOT NULL               | Nom du département (ex. "Ain") |
| region_id     | VARCHAR(10) NOT NULL (FK)   | Clé étrangère vers `regions.region_id` |
| geom          | GEOMETRY(MULTIPOLYGON, 4326) | Contour géographique du département |

*Index spatial :*
```sql
CREATE INDEX idx_departments_geom ON departments USING GIST (geom);
```

---

### **Table `cities`**
Stocke les informations sur les communes de France.

| Champ        | Type                        | Description |
|-------------|----------------------------|-------------|
| city_id     | VARCHAR(10)  (PK)           | Code unique de la commune (ex. "01001" pour L'Abergement-Clémenciat) |
| name        | TEXT NOT NULL               | Nom de la commune |
| department_id | VARCHAR(10) NOT NULL (FK) | Clé étrangère vers `departments.department_id` |
| region_id   | VARCHAR(10) NOT NULL (FK)   | Clé étrangère vers `regions.region_id` |
| geom        | GEOMETRY(MULTIPOLYGON, 4326) | Contour géographique de la commune |

*Index spatial :*
```sql
CREATE INDEX idx_cities_geom ON cities USING GIST (geom);
```

---

## **2. Table des Annonces Immobilières**

### **Table `properties`**
Stocke les annonces immobilières.

| Champ         | Type         | Description                               |
|---------------|-------------|-------------------------------------------|
| property_id   | SERIAL (PK) | Identifiant unique de l'annonce           |
| title         | TEXT        | Titre de l'annonce                        |
| price         | NUMERIC     | Prix du bien                              |
| surface       | NUMERIC     | Surface en m²                             |
| rooms         | INTEGER     | Nombre de pièces                          |
| address       | TEXT        | Adresse du bien                           |
| city_id       | VARCHAR(10) (FK) | Clé étrangère vers `cities.city_id`       |
| publised_date | TIMESTAMP   | Date et heure de publication de l'annonce |
| geom          | GEOMETRY(POINT, 4326) | Localisation géocodée                     |

---

### **Table `property_photos`**
Stocke les photos associées aux annonces immobilières.

| Champ       | Type         | Description |
|------------|-------------|-------------|
| photo_id   | SERIAL (PK) | Identifiant unique de la photo |
| property_id | INTEGER (FK) | Clé étrangère vers `properties.property_id` |
| url        | TEXT        | URL de la photo |

---

## **3. Tables d’Agrégation**

### **Table `agg_city`**
Stocke les statistiques d’agrégation pour chaque commune.

| Champ        | Type        | Description |
|-------------|------------|-------------|
| city_id     | VARCHAR(10) (FK) | Clé étrangère vers `cities.city_id` |
| date_maj    | DATE       | Date de mise à jour |
| avg_price_m2 | NUMERIC   | Prix moyen au m² |
| median_price | NUMERIC   | Prix médian |
| total_properties | INTEGER | Nombre total de biens |

---

### **Table `agg_department`**
Stocke les statistiques d’agrégation pour chaque département.

| Champ        | Type        | Description |
|-------------|------------|-------------|
| department_id | VARCHAR(10) (FK) | Clé étrangère vers `departments.department_id` |
| date_maj    | DATE       | Date de mise à jour |
| avg_price_m2 | NUMERIC   | Prix moyen au m² |
| median_price | NUMERIC   | Prix médian |
| total_properties | INTEGER | Nombre total de biens |

---

### **Table `agg_region`**
Stocke les statistiques d’agrégation pour chaque région.

| Champ        | Type        | Description |
|-------------|------------|-------------|
| region_id   | VARCHAR(10) (FK) | Clé étrangère vers `regions.region_id` |
| date_maj    | DATE       | Date de mise à jour |
| avg_price_m2 | NUMERIC   | Prix moyen au m² |
| median_price | NUMERIC   | Prix médian |
| total_properties | INTEGER | Nombre total de biens |

---

## **Résumé**
- Les **tables géographiques** (`regions`, `departments`, `cities`) sont créées et contiennent les géométries en MULTIPOLYGON pour représenter les contours administratifs de la France.
- **Indexation spatiale** : Des index GIST ont été ajoutés sur les colonnes géométriques pour optimiser les requêtes spatiales.
- **Autres Tables** : Les tables `properties`, `property_photos`, et les tables d’agrégation sont prévues et leur structure est définie.

Cette documentation vous offre une vue d'ensemble de votre schéma actuel et futur, garantissant une cohérence avec PostGIS pour la gestion des données spatiales.