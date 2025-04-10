#!/usr/bin/env python3
import os
import sys
import logging
import spacy
import pymongo
from datetime import datetime
from collections import Counter

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

# Stopwords personnalisés pour éviter les mots peu informatifs
STOPWORDS_ADDITIONNELS = [
    # Verbes génériques
    "faire", "falloir", "voir", "trouver", "aller", "venir", "être", "avoir",
    "pouvoir", "devoir", "mettre", "passer", "rester", "sortir", "vivre", "vie",

    # Mots temporels génériques
    "an", "année", "temps", "fois", "moment", "jour", "mois",

    # Autres mots peu informatifs seuls
    "point", "niveau"
]

# Corrections pour les problèmes de lemmatisation
LEMMA_CORRECTIONS = {
    "manqu": "manque",
    "lycér": "lycée",
    "lycé": "lycée",
    "médiathèqu": "médiathèque",
    "facillté": "facilité",
    "réaménagemer": "réaménagement",
    "pari": "paris"
}

# Normalisation des formes plurielles/singulières et dérivées
NORMALIZE_FORMS = {
    "commun": "commune",
    "communes": "commune",
    "communal": "commune",
    "communale": "commune",
    "communaux": "commune",
    "villages": "village",
    "villageois": "village",
    "commerces": "commerce",
    "commercial": "commerce",
    "commerciaux": "commerce",
    "commerciale": "commerce",
    "scolaire": "école",
    "scolaires": "école",
    "sportifs": "sportif",
    "sportives": "sportif",
    "culturels": "culturel",
    "culturelles": "culturel",
    "transports": "transport"
}

# Charger le modèle SpaCy
def load_spacy_model():
    try:
        nlp = spacy.load("fr_core_news_sm")
        logger.info("SpaCy model loaded successfully")
        return nlp
    except OSError:
        logger.error("Unable to load SpaCy model. Make sure it's installed.")
        sys.exit(1)

# Fonction pour normaliser le texte
def normalize_text(text):
    if not text or not isinstance(text, str):
        return ""

    # Transformation simple sans unicodedata (pour la compatibilité de broadcast)
    text = text.lower()
    # Supprimer les caractères spéciaux et les chiffres
    cleaned_text = ""
    for c in text:
        if c.isalpha() or c.isspace():
            cleaned_text += c
        else:
            cleaned_text += " "

    # Supprimer les espaces multiples
    while "  " in cleaned_text:
        cleaned_text = cleaned_text.replace("  ", " ")

    return cleaned_text.strip()

# Fonction pour vérifier si un mot est dérivé d'un stopword
def is_derived_from_stopword(word):
    for stopword in STOPWORDS_ADDITIONNELS:
        # Vérifier si le mot est une forme dérivée du stopword
        if len(word) > 3 and len(stopword) > 3:
            if word.startswith(stopword[:3]) or stopword.startswith(word[:3]):
                return True
    return False

def extract_significant_words(text, nlp, min_word_length=3):
    if not text or not isinstance(text, str) or len(text) < min_word_length:
        return []

    # Normaliser le texte
    text = normalize_text(text)

    # Analyser avec SpaCy
    doc = nlp(text)

    # Filtrer les mots - version améliorée avec filtrage renforcé
    words = []
    for token in doc:
        lemma = token.lemma_.lower()

        # Exclusion systématique des stopwords et mots de la liste
        if token.is_stop or lemma in STOPWORDS_ADDITIONNELS:
            continue

        # Vérification supplémentaire pour les formes dérivées des stopwords
        if is_derived_from_stopword(lemma):
            continue

        # Filtrage plus sélectif par classe grammaticale
        if token.pos_ in ["NOUN", "ADJ", "PROPN"]:
            if len(token.text) >= min_word_length:
                # Appliquer les corrections de lemmatisation
                if lemma in LEMMA_CORRECTIONS:
                    lemma = LEMMA_CORRECTIONS[lemma]

                # Normaliser les formes plurielles/singulières
                if lemma in NORMALIZE_FORMS:
                    lemma = NORMALIZE_FORMS[lemma]

                words.append(lemma)

    return words

# Fonction pour analyser le sentiment basé sur les notes
def analyze_sentiment(note_globale):
    if note_globale >= 4.0:
        return "positif"
    elif note_globale <= 2.0:
        return "negatif"
    else:
        return "neutre"

# Fonction principale pour traiter les avis avec PySpark
def process_avis(mongo_uri, mongo_db):
    logger.info("Starting processing of feedbacks")

    # Charger le modèle SpaCy
    nlp = load_spacy_model()

    # Récupérer les villes et les avis de MongoDB
    try:
        # Se connecter directement pour trouver les villes non traitées
        client = pymongo.MongoClient(mongo_uri)
        db = client[mongo_db]
        villes_collection = db["villes"]
        avis_collection = db["avis"]
        mots_collection = db["mots_villes"]

        # Récupérer les villes qui n'ont pas encore été traitées
        villes_non_traitees = list(villes_collection.find(
            {"$or": [
                {"statut_traitement": "non_traite"},
                {"statut_traitement": {"$exists": False}}
            ]}
        ))

        logger.info(f"Found {len(villes_non_traitees)} cities to process")

        if not villes_non_traitees:
            logger.info("No cities to process. Exiting.")
            return

        # Traiter chaque ville
        for ville in villes_non_traitees:
            city_id = ville.get("city_id")
            ville_id = ville.get("_id")
            ville_nom = ville.get("nom")

            logger.info(f"Processing avis for {ville_nom} (ID: {city_id})")

            # Récupérer tous les avis pour cette ville
            avis_cursor = avis_collection.find({"city_id": city_id})
            avis_list = list(avis_cursor)

            if not avis_list:
                logger.warning(f"No avis found for {ville_nom}")
                # Marquer la ville comme traitée même si pas d'avis
                villes_collection.update_one(
                    {"_id": ville_id},
                    {"$set": {"statut_traitement": "traite", "date_traitement": datetime.now()}}
                )
                continue

            # Préparer les données pour Spark - extraction manuelle ici pour contourner les limitations de sérialisation
            processed_data = []
            sentiments = {"positif": 0, "neutre": 0, "negatif": 0}

            all_extracted_words = []

            for avis in avis_list:
                description = avis.get("description", "")
                note_globale = avis.get("note_globale", 0)

                # Analyser sentiment
                sentiment = analyze_sentiment(note_globale)
                sentiments[sentiment] += 1

                # Extraire les mots significatifs uniquement de la description
                words_from_description = extract_significant_words(description, nlp)

                # Ajouter les mots extraits à la liste globale
                all_extracted_words.extend(words_from_description)

            # Compter les mots et les trier par fréquence
            word_counts = Counter(all_extracted_words)
            top_words = word_counts.most_common(150)

            # Convertir en format MongoDB
            word_list = [{"mot": word, "poids": count} for word, count in top_words]

            # Calculer les pourcentages
            total_avis = len(avis_list)
            sentiment_percentages = {}
            if total_avis > 0:
                for sentiment, count in sentiments.items():
                    sentiment_percentages[f"{sentiment}_percent"] = round((count / total_avis) * 100, 1)

            # Fusionner les dictionnaires
            sentiment_data = {**sentiments, **sentiment_percentages}

            # Enregistrer dans MongoDB
            try:
                mots_collection.update_one(
                    {"city_id": city_id},
                    {"$set": {
                        "city_id": city_id,
                        "ville_nom": ville_nom,
                        "mots": word_list,
                        "sentiments": sentiment_data,
                        "date_extraction": datetime.now()
                    }},
                    upsert=True
                )

                # Marquer les avis comme traités
                avis_collection.update_many(
                    {"city_id": city_id},
                    {"$set": {"statut_traitement": "traite", "date_traitement": datetime.now()}}
                )

                # Marquer la ville comme traitée
                villes_collection.update_one(
                    {"_id": ville_id},
                    {"$set": {"statut_traitement": "traite", "date_traitement": datetime.now()}}
                )

                logger.info(f"Processing completed for {ville_nom}: {len(word_list)} words extracted")

            except Exception as e:
                logger.error(f"Error saving data for {ville_nom}: {e}")

        logger.info("Processing of avis completed for all cities")

    except Exception as e:
        logger.error(f"Error processing avis: {e}")
    finally:
        if 'client' in locals():
            client.close()

# Programme principal
if __name__ == "__main__":
    # Récupérer les arguments de la ligne de commande
    if len(sys.argv) > 2:
        mongo_uri = sys.argv[1]
        mongo_db = sys.argv[2]
    else:
        mongo_uri = os.environ.get('MONGO_URI', 'mongodb://root:rootpassword@mongodb:27017/')
        mongo_db = os.environ.get('MONGO_DB', 'villes_france')

    logger.info(f"Using MongoDB: {mongo_uri}{mongo_db}")

    try:
        # Traiter les avis
        process_avis(mongo_uri, mongo_db)

    except Exception as e:
        logger.error(f"Error in main processing: {e}")