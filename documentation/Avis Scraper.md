# Documentation: module d'extraction des avis (Scraper)

## Vue d'ensemble

Le module d'extraction des avis (avis-scraper) est responsable de la collecte des données depuis le site biendansmaville.fr. Il récupère à la fois les informations sur les villes françaises et les avis des utilisateurs associés à ces villes.

## Fonctionnement

### Processus d'extraction

1. **Récupération des URLs** : Le scraper commence par extraire la liste des URLs des villes depuis le sitemap du site.
   ```
   https://www.bien-dans-ma-ville.fr/sitemap-villeavis.xml
   ```

2. **Filtrage des URLs** : Seules les URLs au format `ville-code/avis.html` sont conservées. Les quartiers, arrondissements et autres pages sont ignorés.

3. **Extraction des informations sur la ville** :
    - Nom de la ville
    - Code postal
    - Code INSEE (extrait de l'URL)
    - Département (dérivé du code INSEE)
    - Notes moyennes (globale et par catégorie)
    - Nombre d'avis affichés sur le site

4. **Extraction des avis** :
    - Pagination automatique pour récupérer tous les avis
    - Pour chaque avis: auteur, date, note globale, notes par catégorie, description
    - Extraction des votes (pouces haut/bas)

5. **Stockage en base de données** :
    - Les informations sur les villes sont stockées dans la collection `villes`
    - Les avis sont stockés dans la collection `avis`
    - Utilisation de `upsert` pour éviter les duplications

### Gestion du multithreading

Pour optimiser les performances, le scraper utilise une approche par lots avec multithreading :

1. La liste complète des URLs est divisée en lots de taille configurable
2. Chaque lot est traité avec un pool de threads parallèles
3. Le nombre de workers est configurable via `MAX_WORKERS`
4. Une barre de progression (tqdm) affiche l'avancement global

### Mécanismes anti-blocage

Pour éviter d'être bloqué par le site, plusieurs mécanismes sont mis en place :

1. **Délais aléatoires** : Un temps d'attente aléatoire est introduit entre les requêtes.
   ```python
   time.sleep(delay + random.uniform(0.5, 1))
   ```

2. **Headers personnalisés** : Simulation d'un navigateur web.
   ```python
   headers = {
       'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
       'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
       'Referer': 'https://www.bien-dans-ma-ville.fr/',
       ...
   }
   ```

3. **Retry automatique** : En cas d'échec d'une requête, le système réessaie avec un délai croissant.

### Structure de données

#### Collection `villes`
```json
{
  "_id": ObjectId,
  "nom": "Nom de la ville",
  "code_postal": "12345",
  "code_insee": "12345",      // Utilisé comme city_id
  "city_id": "12345",         // Pour mapping avec d'autres sources
  "department_id": "12",      // 2 premiers chiffres du code INSEE
  "url": "https://www.bien-dans-ma-ville.fr/ville-12345/avis.html",
  "notes": {
    "moyenne": 3.5,
    "securite": 3.2,
    "education": 3.8,
    "sport_loisir": 3.5,
    "environnement": 4.0,
    "vie_pratique": 3.6
  },
  "nombre_avis": 42,
  "date_scraping": ISODate,
  "statut_traitement": "non_traite"  // Mis à jour par le processor
}
```

#### Collection `avis`
```json
{
  "_id": ObjectId,
  "ville_id": ObjectId,        // Référence à la collection villes
  "city_id": "12345",          // Code INSEE pour faciliter les jointures
  "avis_id": "avis_123",       // ID unique de l'avis sur le site
  "auteur": "Nom d'utilisateur",
  "date": "01/01/2023",
  "note_globale": 4.0,
  "notes": {
    "securite": 4.0,
    "education": 4.0,
    "sport_loisir": 3.0,
    "environnement": 5.0,
    "vie_pratique": 4.0
  },
  "description": "Texte de l'avis...",
  "pouces_haut": 5,
  "pouces_bas": 1,
  "date_scraping": ISODate,
  "statut_traitement": "non_traite"  // Mis à jour par le processor
}
```

## Modes d'utilisation

Le scraper peut être exécuté dans plusieurs modes différents :

1. **Mode normal** : Extraction de toutes les villes disponibles.
   ```bash
   docker run -e MONGO_URI=mongodb://user:password@mongodb:27017/ avis-scraper
   ```

2. **Mode test** : Extraction d'un ensemble limité de villes pour tester.
   ```bash
   docker run -e TEST_MODE=true avis-scraper
   ```

3. **Mode mise à jour** : Extraction uniquement des nouvelles villes.
   ```bash
   docker run -e UPDATE_MODE=true avis-scraper
   ```

4. **Mode limité** : Extraction d'un nombre limité de villes.
   ```bash
   docker run -e MAX_VILLES=100 avis-scraper
   ```

5. **Mode désactivé** : Utilisation du dump MongoDB au lieu du scraping.
   ```bash
   # Dans docker-compose
   ENABLE_SCRAPER=false USE_MONGODB_DUMP=true docker-compose up
   ```

## Validation des données

Le module inclut un service de validation (`avis-data-validator`) qui effectue plusieurs contrôles sur les données collectées :

1. **Statistiques de base** : Comptage des villes, avis, etc.
2. **Complétude** : Vérification des champs manquants
3. **Cohérence** : Vérification des relations entre collections
4. **Échantillonnage** : Sélection d'exemples pour vérification manuelle

Le rapport de validation est exporté au format JSON :
```json
{
  "date_validation": "2025-03-14T15:59:21.537481",
  "statistiques": {
    "total_villes": 34455,
    "total_avis": 54656
  },
  "completude": {
    "villes_sans_avis": 28978
  },
  "coherence": {
    "villes_notes_incoherentes": 0
  },
  "problemes_potentiels": [
    {
      "type": "villes_sans_avis",
      "description": "28978 villes n'ont aucun avis",
      "severite": "moyenne"
    }
  ]
}
```

## Nettoyage des données

Un script de nettoyage (`cleanup.py`) permet d'identifier et de supprimer les entrées invalides :

1. Identification des entrées ne respectant pas le format d'URL attendu
2. Classification des types d'entrées invalides (quartiers, arrondissements, etc.)
3. Création d'une sauvegarde des entrées à supprimer
4. Suppression des entrées invalides et de leurs avis associés

Le script propose un mode "dry run" qui affiche les actions qui seraient entreprises sans les exécuter.