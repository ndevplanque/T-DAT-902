# Documentation MongoDB - Base de Données Homepedia

## Vue d'ensemble

La base de données MongoDB `villes_france` du projet Homepedia stocke les données d'avis sur les villes françaises collectées depuis le site "bien-dans-ma-ville.fr". Elle constitue le cœur du système de traitement textuel et d'analyse de sentiment, complémentaire aux données géographiques PostgreSQL.

## Architecture générale

### Pipeline de données
Le système MongoDB suit un pipeline de traitement en 3 phases :

1. **Scraping** → Collections `villes` et `avis` (données brutes)
2. **Processing** → Collection `mots_villes` (analyse NLP)  
3. **Aggregation** → Collections `departements_stats` et `regions_stats` (synthèses territoriales)

### Base de données
- **Nom** : `villes_france`
- **URI** : `mongodb://root:rootpassword@mongodb:27017/`
- **Engine** : MongoDB 5.x avec réplication et authentification

## Collections et schémas de données

### 1. Collection `villes` (Données de référence des villes)

**Objectif** : Référentiel des villes françaises avec métadonnées de scraping et notes moyennes.

```javascript
// Schéma de document
{
  "_id": ObjectId("64f8b2a3c4d5e6f7a8b9c0d1"),
  "nom": "Lyon",
  "code_postal": "69001", 
  "code_insee": "69123",
  "city_id": "69123",                    // Clé de liaison avec PostgreSQL
  "department_id": "69",                 // Lien vers département
  "url": "https://www.bien-dans-ma-ville.fr/lyon-69123/avis.html",
  "notes": {
    "moyenne": 3.8,
    "securite": 3.2,
    "education": 4.1,
    "sport_loisir": 3.9,
    "environnement": 3.5,
    "vie_pratique": 4.2
  },
  "nombre_avis": 245,
  "date_scraping": ISODate("2025-06-06T08:06:53.063Z"),
  "statut_traitement": "traite",          // "non_traite", "en_cours", "traite"
  "date_traitement": ISODate("2025-06-06T08:10:15.123Z")
}
```

**Choix de design** :

#### Structure des notes
- **6 dimensions** : Reflète exactement la structure du site source
- **Type Number** : Précision décimale pour les moyennes pondérées
- **Validation** : Notes entre 0.0 et 5.0

#### Statut de traitement
- **Pipeline de workflow** : Évite les retraitements lors des runs incrémentaux
- **États possibles** : 
  - `non_traite` : Ville scrapée mais pas encore analysée
  - `en_cours` : Traitement NLP en cours
  - `traite` : Analyse terminée

#### Clés de liaison
- `city_id` : Code INSEE pour liaison avec PostgreSQL `cities.city_id`
- `department_id` : Facilite les agrégations sans jointure complexe

**Index** :
```javascript
// Index primaires pour les performances
db.villes.createIndex({ "city_id": 1 }, { unique: true })
db.villes.createIndex({ "code_insee": 1 })
db.villes.createIndex({ "department_id": 1 })

// Index de traitement  
db.villes.createIndex({ "statut_traitement": 1 })
```

### 2. Collection `avis` (Avis individuels détaillés)

**Objectif** : Stockage de chaque avis utilisateur avec métadonnées complètes.

```javascript
// Schéma de document
{
  "_id": ObjectId("64f8b2a3c4d5e6f7a8b9c0d2"),
  "ville_id": ObjectId("64f8b2a3c4d5e6f7a8b9c0d1"),
  "city_id": "69123",
  "avis_id": "avis_12345",               // ID unique du site source
  "auteur": "Marie L.",
  "date": "15/03/2024",                  // Format original conservé
  "note_globale": 4.0,
  "notes": {
    "securite": 3.0,
    "education": 4.0,
    "sport_loisir": 4.0,
    "environnement": 4.0,
    "vie_pratique": 5.0
  },
  "description": "Très belle ville avec de nombreux commerces et une bonne qualité de vie. Les transports en commun sont bien développés.",
  "pouces_haut": 15,
  "pouces_bas": 2,
  "date_scraping": ISODate("2025-06-06T08:06:53.063Z"),
  "statut_traitement": "traite",
  "date_traitement": ISODate("2025-06-06T08:15:20.456Z")
}
```

**Choix de design** :

#### Relation avec les villes
- **Double référence** : `ville_id` (ObjectId) ET `city_id` (String)
- **Justification** : Compatibilité avec l'écosystème PostgreSQL tout en gardant les relations MongoDB natives

#### Texte de l'avis
- **Champ `description`** : Texte brut conservé intégralement
- **Pas de préprocessing** : Préservation de l'authenticité pour l'analyse NLP
- **Encoding UTF-8** : Support des caractères spéciaux et accents

#### Métadonnées sociales
- `pouces_haut`/`pouces_bas` : Indicateurs de pertinence communautaire
- **Non utilisé actuellement** : Préparation pour futures analyses de crédibilité

**Index** :
```javascript
// Performance des requêtes
db.avis.createIndex({ "city_id": 1 })
db.avis.createIndex({ "avis_id": 1 })

// Workflow de traitement
db.avis.createIndex({ "statut_traitement": 1 })

// Requêtes analytiques
db.avis.createIndex({ "note_globale": 1 })
db.avis.createIndex({ "date_scraping": 1 })
```

### 3. Collection `mots_villes` (Résultats de l'analyse NLP)

**Objectif** : Mots-clés extraits et analyse de sentiment par ville après traitement SpaCy.

```javascript
// Schéma de document
{
  "_id": ObjectId("64f8b2a3c4d5e6f7a8b9c0d3"),
  "city_id": "69123",
  "ville_nom": "Lyon",
  "mots": [
    {"mot": "transport", "poids": 156},
    {"mot": "commerce", "poids": 142},
    {"mot": "culture", "poids": 98},
    {"mot": "sécurité", "poids": 87},
    {"mot": "école", "poids": 76},
    {"mot": "calme", "poids": 65}
  ],
  "sentiments": {
    "positif": 89,                       // Nombre d'avis positifs (note ≥ 4.0)
    "neutre": 125,                       // Nombre d'avis neutres (2.0 < note < 4.0)
    "negatif": 31,                       // Nombre d'avis négatifs (note ≤ 2.0)
    "positif_percent": 36.3,
    "neutre_percent": 51.0,
    "negatif_percent": 12.7
  },
  "date_extraction": ISODate("2025-06-06T08:20:15.789Z")
}
```

**Choix de design** :

#### Algorithme d'extraction des mots-clés
**Pipeline SpaCy** :
1. **Tokenisation** avec modèle français `fr_core_news_sm`
2. **Lemmatisation** : "transports" → "transport"
3. **Filtrage linguistique** :
   - Exclusion des stop words français
   - Suppression des entités nommées (villes, personnes)
   - Minimum 3 caractères
4. **Pondération TF** : Comptage des occurrences par terme

#### Structure des mots-clés
- **Array de objets** : Plus efficace que les clés dynamiques pour les requêtes
- **Ordre par poids** : Tri décroissant pour optimiser l'affichage frontend
- **Limitation** : Top 50 mots conservés par ville

#### Calcul des sentiments
**Règles métier** :
```javascript
// Algorithme de classification
note_globale >= 4.0 → sentiment "positif"
2.0 < note_globale < 4.0 → sentiment "neutre"  
note_globale <= 2.0 → sentiment "négatif"
```

**Justification** : Seuils basés sur l'analyse de la distribution des notes réelles

**Index** :
```javascript
// Clé unique par ville
db.mots_villes.createIndex({ "city_id": 1 }, { unique: true })

// Optimisation des requêtes de mots-clés
db.mots_villes.createIndex({ "mots.poids": -1 })
```

### 4. Collection `departements_stats` (Agrégations départementales)

**Objectif** : Synthèse statistique des avis au niveau département pour l'API territoriale.

```javascript
// Schéma de document
{
  "_id": "69",
  "department_id": "69",
  "nom": "Rhône", 
  "region_id": "84",                     // Lien vers région
  "nombre_villes": 342,                  // Villes avec au moins un avis
  "nombre_avis": 4580,
  "notes": {
    "moyenne": 3.7,                      // Moyenne pondérée par nombre d'avis
    "securite": 3.2,
    "education": 4.0,
    "sport_loisir": 3.8,
    "environnement": 3.4,
    "vie_pratique": 4.1
  },
  "sentiments": {
    "positif": 1658,
    "neutre": 2377,
    "negatif": 545,
    "positif_percent": 36.2,
    "neutre_percent": 51.9,
    "negatif_percent": 11.9
  },
  "mots": [                              // Top 30 mots du département
    {"mot": "transport", "poids": 2890},
    {"mot": "commerce", "poids": 2456}, 
    {"mot": "culture", "poids": 1823},
    {"mot": "école", "poids": 1654}
  ],
  "date_extraction": ISODate("2025-06-06T08:25:30.123Z")
}
```

**Algorithme d'agrégation** :

#### Moyennes pondérées
```javascript
// Pipeline MongoDB pour le calcul des moyennes
[
  { $match: { "statut_traitement": "traite" } },
  { $group: {
      _id: "$department_id",
      moyenne: { 
        $sum: { 
          $multiply: ["$notes.moyenne", "$nombre_avis"] 
        }
      },
      total_avis: { $sum: "$nombre_avis" }
  }},
  { $project: {
      moyenne_ponderee: { $divide: ["$moyenne", "$total_avis"] }
  }}
]
```

#### Agrégation des mots-clés
**Fusion et tri** : Sommation des poids + tri décroissant
**Seuil de pertinence** : Minimum 5 occurrences pour filtrer le bruit

### 5. Collection `regions_stats` (Agrégations régionales)

**Objectif** : Synthèse statistique au niveau régional, niveau le plus élevé de l'analyse territoriale.

```javascript
// Schéma de document  
{
  "_id": "84",
  "region_id": "84",
  "nom": "Auvergne-Rhône-Alpes",
  "nombre_departements": 12,             // Départements avec données
  "nombre_villes": 1287,                 // Villes avec au moins un avis
  "nombre_avis": 23456,
  "notes": {
    "moyenne": 3.6,                      // Moyenne pondérée régionale
    "securite": 3.1,
    "education": 3.9,
    "sport_loisir": 3.7,
    "environnement": 3.3,
    "vie_pratique": 4.0
  },
  "sentiments": {
    "positif": 8485,
    "neutre": 12178, 
    "negatif": 2793,
    "positif_percent": 36.2,
    "neutre_percent": 51.9,
    "negatif_percent": 11.9
  },
  "mots": [                              // Top 50 mots de la région
    {"mot": "transport", "poids": 15678},
    {"mot": "commerce", "poids": 13234},
    {"mot": "culture", "poids": 9876},
    {"mot": "montagne", "poids": 8234}   // Mots spécifiques à la région
  ],
  "departements": [                      // Liste des départements contributeurs
    {"department_id": "01", "nom": "Ain"},
    {"department_id": "07", "nom": "Ardèche"},
    {"department_id": "69", "nom": "Rhône"}
  ],
  "date_extraction": ISODate("2025-06-06T08:30:45.456Z")
}
```

**Index pour les agrégations** :
```javascript
// Performance des requêtes API
db.departements_stats.createIndex({ "department_id": 1 }, { unique: true })
db.departements_stats.createIndex({ "region_id": 1 })
db.departements_stats.createIndex({ "notes.moyenne": -1 })

db.regions_stats.createIndex({ "region_id": 1 }, { unique: true })
db.regions_stats.createIndex({ "notes.moyenne": -1 })
```

## Stratégies de performance et indexation

### Index composites pour les requêtes complexes
```javascript
// Recherche géographique + statut
db.villes.createIndex({ 
  "department_id": 1, 
  "statut_traitement": 1 
})

// Tri par qualité + localisation  
db.villes.createIndex({
  "region_id": 1,
  "notes.moyenne": -1
})

// Requêtes temporelles sur les avis
db.avis.createIndex({
  "city_id": 1,
  "date_scraping": -1
})
```

### Optimisations spécifiques

#### Taille des documents
- **Limitation des mots-clés** : Top 30-50 par entité pour éviter les documents volumineux
- **Pagination** : Curseur sur `date_scraping` pour les imports incrementaux

#### Requêtes fréquentes
- **Cache applicatif** : TTL de 1h sur les agrégations départementales/régionales
- **Index sparses** : Uniquement sur les documents avec données (`sparse: true`)

## Liaison avec PostgreSQL

### Clés de correspondance
```javascript
// Correspondances entre les systèmes
MongoDB.villes.city_id ↔ PostgreSQL.cities.city_id
MongoDB.villes.department_id ↔ PostgreSQL.departments.department_id  
MongoDB.departements_stats.region_id ↔ PostgreSQL.regions.region_id
```

### Synchronisation des référentiels
**Workflow** : 
1. PostgreSQL = source de vérité pour la géographie
2. MongoDB = source de vérité pour les avis et sentiments
3. Agrégateur = point de fusion des deux systèmes

## Pipeline ETL et workflow

### 1. Phase Scraping (avis-scraper)
```javascript
// Configuration scraper
MAX_VILLES = 0              // 0 = toutes les villes
MAX_WORKERS = 8             // Parallélisation
UPDATE_MODE = true          // Mode incrémental
```

**Gestion des doublons** :
```javascript
// Upsert automatique
db.villes.updateOne(
  { "city_id": ville.city_id },
  { $set: ville_data },
  { upsert: true }
)
```

### 2. Phase Processing (avis-processor)  
**Critères de sélection** :
```javascript
// Villes à traiter
{ $or: [
  { "statut_traitement": { $exists: false } },
  { "statut_traitement": "non_traite" }
]}
```

**Traitement distribué** : 
- **Spark Workers** : 2 workers avec 8G RAM chacun
- **Partitioning** : Par department_id pour équilibrer la charge

### 3. Phase Aggregation (data-aggregator)
**Calculs temps réel** vs **précalculés** :
- ✅ **Précalculés** : Moyennes, pourcentages, top mots-clés
- ⚡ **Temps réel** : Recherche textuelle, filtres avancés

## Volumétrie et statistiques

### Données actuelles (juin 2025)
- **Villes référencées** : 34,455 (toutes les communes françaises)
- **Villes avec avis** : 5,477 (16%)
- **Avis collectés** : 54,656 
- **Mots-clés extraits** : 368,672 (moyenne 35.6 mots/ville)

### Répartition territoriale
- **Départements avec données** : 94/109 (86%)
- **Régions avec données** : 12/26 (46%)

### Distribution des sentiments
- **Positifs** : 36.15% des avis
- **Neutres** : 51.87% des avis  
- **Négatifs** : 11.99% des avis

## Sauvegarde et maintenance

### Dumps MongoDB
```bash
# Sauvegarde complète
mongodump --host mongodb --port 27017 --username root --password rootpassword --db villes_france --out /backup/

# Restauration
mongorestore --host mongodb --port 27017 --username root --password rootpassword --db villes_france /backup/villes_france/

# Dump spécifique pour la prod
mongodump --collection villes --out /backup/villes_only/
```

### Scripts de maintenance
```javascript
// Nettoyage des anciens traitements
db.villes.updateMany(
  { "date_traitement": { $lt: ISODate("2025-01-01") } },
  { $set: { "statut_traitement": "non_traite" } }
)

// Réindexation périodique
db.mots_villes.reIndex()
db.departements_stats.reIndex()
```

### Monitoring des performances
```javascript
// Statistiques d'utilisation des index
db.villes.aggregate([{ $indexStats: {} }])

// Requêtes lentes
db.setProfilingLevel(2, { slowms: 1000 })
db.system.profile.find().sort({ ts: -1 }).limit(5)
```

## Sécurité et accès

### Authentification
```javascript
// Utilisateur applicatif (lecture seule)
db.createUser({
  user: "homepedia_read",
  pwd: "secure_password",
  roles: [{ role: "read", db: "villes_france" }]
})

// Utilisateur ETL (lecture/écriture)  
db.createUser({
  user: "homepedia_etl", 
  pwd: "secure_password",
  roles: [{ role: "readWrite", db: "villes_france" }]
})
```

### Validation des schémas
```javascript
// Exemple de validation pour la collection villes
db.createCollection("villes", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["city_id", "nom", "department_id"],
      properties: {
        city_id: { bsonType: "string" },
        notes: {
          bsonType: "object",
          properties: {
            moyenne: { bsonType: "double", minimum: 0, maximum: 5 }
          }
        }
      }
    }
  }
})
```

Cette architecture MongoDB garantit :
- **Flexibilité** : Schema-less pour l'évolution des formats d'avis
- **Performance** : Index optimisés pour les requêtes API géolocalisées  
- **Scalabilité** : Structure préparée pour le sharding par région
- **Cohérence** : Pipeline ETL robuste avec gestion des états de traitement