# Documentation : module de traitement des avis (Processor)

## Vue d'ensemble

Le module de traitement des avis (avis-processor) analyse les avis collectés pour en extraire les mots significatifs et analyser les sentiments. Il utilise des techniques de traitement du langage naturel (NLP) avec SpaCy et s'exécute dans un environnement Apache Spark pour le traitement distribué.

## Fonctionnement

### Extraction des mots significatifs

Le processus d'extraction des mots significatifs comprend plusieurs étapes :

1. **Normalisation du texte** :
    - Mise en minuscule
    - Suppression des caractères spéciaux et chiffres
    - Suppression des espaces multiples

   ```python
   def normalize_text(text):
       if not text or not isinstance(text, str):
           return ""
       
       text = text.lower()
       cleaned_text = ""
       for c in text:
           if c.isalpha() or c.isspace():
               cleaned_text += c
           else:
               cleaned_text += " "
       
       while "  " in cleaned_text:
           cleaned_text = cleaned_text.replace("  ", " ")
       
       return cleaned_text.strip()
   ```

2. **Analyse linguistique avec SpaCy** :
    - Tokenisation du texte
    - Analyse grammaticale (part-of-speech tagging)
    - Lemmatisation (réduction des mots à leur forme canonique)

3. **Filtrage des mots** :
    - Élimination des stopwords (mots fréquents non informatifs)
    - Filtrage par classe grammaticale (noms, adjectifs, entités nommées)
    - Exclusion des mots trop courts
    - Exclusion des mots personnalisés (liste de stopwords additionnels)

   ```python
   # Extrait du code de filtrage
   if token.is_stop or lemma in STOPWORDS_ADDITIONNELS:
       continue
       
   if is_derived_from_stopword(lemma):
       continue
       
   if token.pos_ in ["NOUN", "ADJ", "PROPN"]:
       if len(token.text) >= min_word_length:
           # Mot conservé
   ```

4. **Normalisation des formes** :
    - Correction des problèmes de lemmatisation
    - Normalisation des formes plurielles/singulières
    - Regroupement des dérivés (ex: "communal", "communale", "commune" → "commune")

   ```python
   # Corrections pour les problèmes de lemmatisation
   LEMMA_CORRECTIONS = {
       "manqu": "manque",
       "lycér": "lycée",
       "médiathèqu": "médiathèque",
       ...
   }
   
   # Normalisation des formes plurielles/singulières
   NORMALIZE_FORMS = {
       "commun": "commune",
       "communes": "commune",
       "communal": "commune",
       "commerces": "commerce",
       ...
   }
   ```

### Analyse des sentiments

L'analyse des sentiments est basée sur les notes attribuées par les utilisateurs.

Pour chaque ville, le système :
1. Calcule le nombre d'avis positifs, neutres et négatifs
2. Convertit ces nombres en pourcentages
3. Stocke ces informations dans la collection `mots_villes`

### Traitement des villes

Le processeur traite les villes une par une, selon ce flux :

1. **Sélection des villes non traitées** :
   ```python
   villes_non_traitees = list(villes_collection.find({
       "$or": [
           {"statut_traitement": "non_traite"},
           {"statut_traitement": {"$exists": False}}
       ]
   }))
   ```

2. **Pour chaque ville** :
    - Récupération de tous les avis associés
    - Extraction des mots significatifs de chaque avis
    - Comptage des mots et calcul de leur fréquence
    - Analyse du sentiment global
    - Stockage des résultats dans MongoDB
    - Mise à jour du statut de traitement

3. **Agrégation et stockage** :
    - Les mots sont triés par fréquence (poids)
    - Les 150 mots les plus fréquents sont conservés
    - Les données sont stockées dans la collection `mots_villes`
    - Les collections `villes` et `avis` sont mises à jour

### Utilisation d'Apache Spark

Le processeur s'exécute dans un environnement Apache Spark pour permettre le traitement distribué des données :

1. **Initialisation de SparkSession** :
   ```python
   def init_spark():
       spark = SparkSession.builder \
           .appName("AvisProcessor") \
           .config("spark.mongodb.input.uri", mongo_uri + mongo_db) \
           .config("spark.mongodb.output.uri", mongo_uri + mongo_db) \
           .getOrCreate()
       return spark
   ```

2. **Configuration du connecteur MongoDB** :
    - Le connecteur Spark pour MongoDB est installé
    - Les pilotes MongoDB sont téléchargés et configurés
    - Les bibliothèques Python nécessaires sont installées

3. **Soumission du job** :
    - Le script `submit.sh` soumet le job de traitement à Spark
    - Le traitement peut être distribué sur plusieurs workers
    - Les résultats sont écrits directement dans MongoDB

### Structure de données

#### Collection `mots_villes`
```json
{
  "_id": ObjectId,
  "city_id": "12345",                 // Code INSEE de la ville
  "ville_nom": "Nom de la ville",
  "mots": [
    {"mot": "commerce", "poids": 15},  // Poids = fréquence du mot
    {"mot": "école", "poids": 12},
    {"mot": "transport", "poids": 10},
    ...
  ],
  "sentiments": {
    "positif": 25,                    // Nombre d'avis positifs
    "neutre": 10,                     // Nombre d'avis neutres
    "negatif": 5,                     // Nombre d'avis négatifs
    "positif_percent": 62.5,          // Pourcentage d'avis positifs
    "neutre_percent": 25.0,           // Pourcentage d'avis neutres
    "negatif_percent": 12.5           // Pourcentage d'avis négatifs
  },
  "date_extraction": ISODate           // Date du traitement
}
```

## Vérification et Validation

### Validation du traitement

Le script `verify_processing.py` effectue plusieurs analyses pour vérifier la qualité du traitement :

1. **Statistiques générales** :
    - Nombre de villes traitées/non traitées
    - Nombre total de mots extraits
    - Moyenne de mots par ville

2. **Distribution des sentiments** :
    - Sentiment positif/neutre/négatif moyen
    - Distribution des sentiments par ville (histogramme)

3. **Analyse des mots fréquents** :
    - Top 50 des mots les plus fréquents
    - Visualisation des 30 mots les plus fréquents (graphique à barres)

4. **Vérification de cohérence** :
    - Échantillonnage de villes pour vérifier la cohérence entre mots et sentiments
    - Vérification que les mots extraits correspondent au sentiment global

### Résultats actuels

Les résultats actuels du traitement montrent :

```
===== STATISTIQUES GÉNÉRALES =====
Total des villes: 34455
Villes traitées: 34455 (100.0%)
Total des mots extraits: 368672
Moyenne de mots par ville: 35.61

===== DISTRIBUTION DES SENTIMENTS =====
Sentiment positif moyen: 36.15%
Sentiment neutre moyen: 51.87%
Sentiment négatif moyen: 11.99%
```

Les mots les plus fréquents sont :
1. "ville" (dominant largement)
2. "commerce"
3. "petit"
4. "bon"
5. "agréable"

### Exemples de cohérence

Pour montrer la cohérence entre les sentiments et les mots extraits, voici des exemples :

**Ville avec sentiment positif élevé** :
```
Avis Gradignan 33170
Sentiments: Positif 90.5%, Neutre 9.5%, Négatif 0.0%
Top mots: ville, bordeaux, centre, parc, agréable, commerce...
```

**Ville avec sentiment mixte** :
```
Avis Montévrain 77144
Sentiments: Positif 69.2%, Neutre 23.1%, Négatif 7.7%
Top mots: ville, commerce, paris, centre, bourg, bon...
```