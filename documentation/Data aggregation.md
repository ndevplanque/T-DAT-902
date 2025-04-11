# Documentation du Module d'Agrégation de Données

## Vue d'ensemble

Le module d'agrégation est responsable de la consolidation des données de villes scrappées depuis biendansmaville.fr en statistiques agrégées par département et par région. Ce module fait partie d'un pipeline de traitement plus large qui comprend le scraping, le traitement des avis et la visualisation.

## Architecture

Le module est constitué de deux composants principaux :

1. **data-aggregator** : Service principal qui agrège les données des villes au niveau des départements et des régions
2. **data-aggregator-validator** : Service de validation qui vérifie l'intégrité et la cohérence des données agrégées

Ces services s'intègrent dans l'architecture globale du projet en consommant des données de:
- MongoDB (données scrappées des villes et des avis)
- PostgreSQL (informations géographiques des départements et régions)

## Flux de données

```
Villes (MongoDB) ──┐
                   │
                   v
           Agrégation par Département
                   │
                   v
        Départements (MongoDB) ──┐
                                 │
                                 v
                       Agrégation par Région
                                 │
                                 v
                        Régions (MongoDB)
```

## Processus d'agrégation

### Agrégation par département

Le processus d'agrégation par département fonctionne comme suit:

1. Sélection des villes ayant au moins un avis et un department_id valide
2. Calcul des statistiques par département:
    - Nombre de villes
    - Nombre total d'avis
    - Notes moyennes (globale, sécurité, éducation, etc.)
3. Agrégation des sentiments (positifs, neutres, négatifs)
4. Extraction des mots les plus fréquents
5. Stockage dans la collection `departements_stats` de MongoDB

### Agrégation par région

Le processus d'agrégation par région utilise les données départementales:

1. Regroupement des départements par région
2. Calcul des notes moyennes pondérées par le nombre de villes
3. Agrégation des sentiments
4. Consolidation des mots fréquents
5. Stockage dans la collection `regions_stats` de MongoDB

## Méthodes de calcul

### Notes moyennes

- **Niveau département**: Moyenne arithmétique des notes des villes du département
  ```python
  moyenne_departement = avg(notes_villes)
  ```

- **Niveau région**: Moyenne pondérée par le nombre de villes dans chaque département
  ```python
  moyenne_region = sum(note_dept * nb_villes_dept) / sum(nb_villes_dept)
  ```

### Analyse des sentiments

Pour chaque niveau (département/région), les sentiments sont agrégés en:
- Comptage brut (nombre de sentiments positifs, neutres, négatifs)
- Pourcentages (proportion de chaque type de sentiment)

### Extraction des mots fréquents

1. **Niveau département**: Agrégation des mots des villes avec leur poids
2. **Niveau région**: Consolidation des mots fréquents de tous les départements
    - Utilisation d'un `Counter` pour additionner les poids des mots identiques
    - Sélection des 50 mots les plus fréquents

## Validation des données

Le module de validation effectue les vérifications suivantes:

1. **Vérifications structurelles**:
    - Présence de toutes les collections requises
    - Structure correcte des documents (champs obligatoires présents)

2. **Vérifications de cohérence**:
    - Cohérence entre les mapping département-région dans MongoDB et PostgreSQL
    - Cohérence dans le nombre total d'avis entre les différents niveaux
    - Vérification que les notes sont dans une plage valide (0-10)
    - Validation que les pourcentages de sentiments totalisent 100%

3. **Détection d'anomalies**:
    - Départements sans villes
    - Régions sans départements
    - Notes extrêmes
    - Distributions de sentiment inhabituelles
    - Mots étrangement courts ou longs

4. **Génération de rapports**:
    - Visualisations graphiques (distribution des notes, sentiments, etc.)
    - Rapport HTML récapitulatif
    - Fichier JSON avec les statistiques clés

## Limitations connues

- Les données agrégées ne reflètent que les villes présentes sur biendansmaville.fr, ce qui crée des différences avec les données officielles
- Certains départements ou régions peuvent être absents si aucune ville correspondante n'est trouvée sur le site source
- Le nombre de villes dans les agrégations peut différer du nombre officiel de communes en France

## Points techniques importants

1. **Dépendances**:
    - MongoDB pour le stockage des données scrappées et agrégées
    - PostgreSQL pour les informations géographiques

2. **Collections MongoDB**:
    - `villes`: Données brutes des villes
    - `avis`: Avis individuels
    - `mots_villes`: Analyse des mots par ville
    - `departements_stats`: Statistiques agrégées par département
    - `regions_stats`: Statistiques agrégées par région

3. **Variables d'environnement**:
    - `MONGO_URI`: URI de connexion à MongoDB
    - `MONGO_DB`: Nom de la base de données
    - `POSTGRES_DB/USER/PASSWORD/HOST/PORT`: Configuration PostgreSQL
    - `OUTPUT_DIR`: Répertoire de sortie pour les rapports de validation

## Structure des données agrégées

### Exemple de document `departements_stats`

```json
{
  _id: '62',
  date_extraction: ISODate('2025-04-11T13:53:34.695Z'),
  department_id: '62',
  mots: [
    { mot: 'ville', poids: 1109 },
    { mot: 'commerce', poids: 313 },
    { mot: 'petit', poids: 231 },
    { mot: 'bon', poids: 226 },
    { mot: 'agréable', poids: 175 },
    { mot: 'centre', poids: 159 },
    { mot: 'grand', poids: 152 },
    { mot: 'proximité', poids: 134 },
    ...
  ],
  nom: 'Pas-de-Calais',
  nombre_avis: 1076,
  nombre_villes: 164,
  notes: {
    moyenne: 3.4,
    securite: 3.5,
    education: 3.6,
    sport_loisir: 3.3,
    environnement: 3.4,
    vie_pratique: 3.1
  },
  region_id: '32',
  sentiments: {
    positif: 335,
    neutre: 590,
    negatif: 151,
    positif_percent: 31.1,
    neutre_percent: 54.8,
    negatif_percent: 14
  }
}
```

### Exemple de document `regions_stats`

```json
{
  _id: '11',
  date_extraction: ISODate('2025-04-11T13:53:35.820Z'),
  departements: [
    { department_id: '75', nom: 'Paris' },
    { department_id: '77', nom: 'Seine-et-Marne' },
    { department_id: '78', nom: 'Yvelines' },
    { department_id: '91', nom: 'Essonne' },
    { department_id: '92', nom: 'Hauts-de-Seine' },
    { department_id: '93', nom: 'Seine-Saint-Denis' },
    { department_id: '94', nom: 'Val-de-Marne' },
    { department_id: '95', nom: "Val-d'Oise" }
  ],
  mots: [
    { mot: 'ville', poids: 15299 },
    { mot: 'commerce', poids: 3780 },
    { mot: 'paris', poids: 2916 },
    { mot: 'bon', poids: 2457 },
    { mot: 'agréable', poids: 2318 },
    { mot: 'centre', poids: 2314 },
    { mot: 'transport', poids: 2069 },
    { mot: 'quartier', poids: 1976 },
    { mot: 'petit', poids: 1855 },
    { mot: 'proximité', poids: 1558 },
    ...
  ],
  nom: 'Île-de-France',
  nombre_avis: 11677,
  nombre_departements: 8,
  nombre_villes: 625,
  notes: {
    moyenne: 3.4,
    securite: 3.5,
    education: 3.5,
    sport_loisir: 3.3,
    environnement: 3.7,
    vie_pratique: 3.2
  },
  region_id: '11',
  sentiments: {
    positif: 4224,
    neutre: 5376,
    negatif: 2051,
    positif_percent: 36.3,
    neutre_percent: 46.1,
    negatif_percent: 17.6
  }
}
```

## Utilisation

### Démarrage du processus d'agrégation

```bash
docker-compose up data-aggregator
```

### Validation des données

```bash
docker-compose up data-aggregator-validator
```

Les résultats de validation sont disponibles dans le répertoire `./data-aggregator/validation/results`.