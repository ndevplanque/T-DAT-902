# What the validation script does :
#
# Basic Statistics
#
## Counts total cities and reviews
## Calculates average reviews per city
## Identifies cities with most/least reviews
## Shows top 10 cities by review count
#
#
# Data Completeness
#
## Identifies cities with no reviews
## Finds missing fields in cities and reviews
## Counts empty descriptions
#
#
# Data Consistency
#
## Checks for orphaned reviews (no matching city)
## Compares calculated vs. stored average ratings
## Identifies discrepancies between them
#
#
# Random Sampling
#
## Selects random cities for manual verification
##     Shows sample reviews for each
##     Makes it easy to compare with the website manually
#
#
# Rating Analysis
#
## Shows distribution of ratings (how many 1-star, 2-star, etc.)
## Compares ratings across categories
## Identifies best/worst rated departments
#
#
# Exports Results
#
## Creates a JSON report with all findings
## Highlights potential data quality issues

import pymongo
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import random
import os
import logging
import json

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/validation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

def connect_to_mongodb():
    """Connexion à la base MongoDB"""
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://root:rootpassword@mongodb:27017/')
    mongo_db = os.environ.get('MONGO_DB', 'villes_france')

    try:
        client = pymongo.MongoClient(mongo_uri)
        db = client[mongo_db]
        avis_collection = db["avis"]
        villes_collection = db["villes"]

        return client, avis_collection, villes_collection
    except Exception as e:
        logger.error(f"Erreur de connexion à MongoDB: {e}")
        return None, None, None

def check_basic_statistics(villes_collection, avis_collection):
    """Vérifier les statistiques de base"""
    print("=== STATISTIQUES DE BASE ===")

    # Nombre total de villes
    total_villes = villes_collection.count_documents({})
    print(f"Nombre total de villes: {total_villes}")

    # Nombre total d'avis
    total_avis = avis_collection.count_documents({})
    print(f"Nombre total d'avis: {total_avis}")

    # Moyenne d'avis par ville
    moyenne_avis = total_avis / total_villes if total_villes > 0 else 0
    print(f"Moyenne d'avis par ville: {moyenne_avis:.2f}")

    # Répartition du nombre d'avis par ville
    pipeline = [
        {"$group": {"_id": "$ville_id", "count": {"$sum": 1}}},
        {"$group": {"_id": None,
                    "min": {"$min": "$count"},
                    "max": {"$max": "$count"},
                    "avg": {"$avg": "$count"},
                    "median": {"$avg": "$count"}}}
    ]
    result = list(avis_collection.aggregate(pipeline))
    if result:
        stats = result[0]
        print(f"Répartition des avis par ville:")
        print(f"  - Minimum: {stats['min']}")
        print(f"  - Maximum: {stats['max']}")
        print(f"  - Moyenne: {stats['avg']:.2f}")

    # Top 10 des villes avec le plus d'avis
    pipeline = [
        {"$group": {"_id": "$ville_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
        {"$lookup": {
            "from": "villes",
            "localField": "_id",
            "foreignField": "_id",
            "as": "ville_info"
        }},
        {"$unwind": {"path": "$ville_info", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "ville": "$ville_info.nom",
            "code_postal": "$ville_info.code_postal",
            "nombre_avis": "$count"
        }}
    ]

    top_villes = list(avis_collection.aggregate(pipeline))
    print("\nTop 10 des villes avec le plus d'avis:")
    for idx, ville in enumerate(top_villes, 1):
        print(f"{idx}. {ville.get('ville', 'N/A')} ({ville.get('code_postal', 'N/A')}): {ville.get('nombre_avis', 0)} avis")

def check_data_completeness(villes_collection, avis_collection):
    """Vérifier la complétude des données"""
    print("\n=== VÉRIFICATION DE LA COMPLÉTUDE ===")

    # Villes sans avis
    pipeline = [
        {"$lookup": {
            "from": "avis",
            "localField": "_id",
            "foreignField": "ville_id",
            "as": "avis"
        }},
        {"$match": {"avis": {"$size": 0}}},
        {"$count": "villes_sans_avis"}
    ]

    result = list(villes_collection.aggregate(pipeline))
    villes_sans_avis = result[0]["villes_sans_avis"] if result else 0
    print(f"Villes sans avis: {villes_sans_avis}")

    # Vérifier les champs manquants dans les villes
    villes_champs = [
        "nom", "code_postal", "code_insee", "city_id",
        "department_id", "url", "notes", "nombre_avis"
    ]

    for champ in villes_champs:
        missing = villes_collection.count_documents({champ: {"$exists": False}})
        print(f"Villes sans le champ '{champ}': {missing}")

    # Vérifier les notes manquantes
    note_fields = ["moyenne", "securite", "education", "sport_loisir", "environnement", "vie_pratique"]
    for note in note_fields:
        missing = villes_collection.count_documents({f"notes.{note}": {"$exists": False}})
        print(f"Villes sans note '{note}': {missing}")

    # Vérifier les champs manquants dans les avis
    avis_champs = [
        "ville_id", "city_id", "avis_id", "auteur",
        "date", "note_globale", "notes", "description"
    ]

    for champ in avis_champs:
        missing = avis_collection.count_documents({champ: {"$exists": False}})
        print(f"Avis sans le champ '{champ}': {missing}")

    # Vérifier les descriptions vides
    avis_vides = avis_collection.count_documents({"description": ""})
    print(f"Avis avec description vide: {avis_vides}")

def check_data_consistency(villes_collection, avis_collection):
    """Vérifier la cohérence des données"""
    print("\n=== VÉRIFICATION DE LA COHÉRENCE ===")

    # Vérifier si tous les city_id des avis existent dans la collection des villes
    pipeline = [
        {"$group": {"_id": "$city_id"}},
        {"$lookup": {
            "from": "villes",
            "localField": "_id",
            "foreignField": "city_id",
            "as": "ville_match"
        }},
        {"$match": {"ville_match": {"$size": 0}}},
        {"$count": "orphan_city_ids"}
    ]

    result = list(avis_collection.aggregate(pipeline))
    orphan_city_ids = result[0]["orphan_city_ids"] if result else 0
    print(f"Avis avec city_id orphelins (sans ville correspondante): {orphan_city_ids}")

    # Vérifier la cohérence des notes moyennes
    pipeline = [
        {"$group": {
            "_id": "$city_id",
            "calculated_avg": {"$avg": "$note_globale"},
            "count": {"$sum": 1}
        }},
        {"$lookup": {
            "from": "villes",
            "localField": "_id",
            "foreignField": "city_id",
            "as": "ville"
        }},
        {"$unwind": {"path": "$ville", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "city_id": "$_id",
            "calculated_avg": 1,
            "stored_avg": "$ville.notes.moyenne",
            "difference": {"$abs": {"$subtract": ["$calculated_avg", "$ville.notes.moyenne"]}},
            "count": 1
        }},
        {"$match": {"difference": {"$gt": 0.5}}},  # Écart significatif
        {"$sort": {"difference": -1}},
        {"$limit": 10}
    ]

    inconsistent_notes = list(avis_collection.aggregate(pipeline))
    print(f"\nVilles avec écart significatif entre notes calculées et stockées: {len(inconsistent_notes)}")
    for idx, item in enumerate(inconsistent_notes[:5], 1):
        print(f"{idx}. City ID: {item['city_id']}, Calculée: {item['calculated_avg']:.2f}, Stockée: {item['stored_avg']:.2f}, Écart: {item['difference']:.2f}")

def random_sampling(villes_collection, avis_collection):
    """Échantillonnage aléatoire pour vérification manuelle"""
    print("\n=== ÉCHANTILLONNAGE ALÉATOIRE POUR VÉRIFICATION ===")

    # Sélectionner 5 villes aléatoires
    sample_size = 5
    total_villes = villes_collection.count_documents({})

    if total_villes == 0:
        print("Aucune ville trouvée dans la base de données.")
        return

    random_villes = []

    pipeline = [{"$sample": {"size": sample_size}}]
    ville_samples = list(villes_collection.aggregate(pipeline))

    print(f"Échantillon de {len(ville_samples)} villes:")
    for idx, ville in enumerate(ville_samples, 1):
        # Compter le nombre d'avis pour cette ville
        avis_count = avis_collection.count_documents({"ville_id": ville["_id"]})

        print(f"\n{idx}. {ville.get('nom', 'N/A')} ({ville.get('code_postal', 'N/A')})")
        print(f"   - URL: {ville.get('url', 'N/A')}")
        print(f"   - Code INSEE: {ville.get('code_insee', 'N/A')}")
        print(f"   - Note moyenne: {ville.get('notes', {}).get('moyenne', 'N/A')}")
        print(f"   - Nombre d'avis dans la base: {avis_count}")
        print(f"   - Nombre d'avis indiqué sur le site: {ville.get('nombre_avis', 'N/A')}")

        # Échantillon d'avis pour cette ville
        if avis_count > 0:
            sample_avis = list(avis_collection.aggregate([
                {"$match": {"ville_id": ville["_id"]}},
                {"$sample": {"size": min(3, avis_count)}}
            ]))

            print(f"   - Échantillon d'avis:")
            for avis_idx, avis in enumerate(sample_avis, 1):
                print(f"     {avis_idx}. Auteur: {avis.get('auteur', 'N/A')}")
                print(f"        Date: {avis.get('date', 'N/A')}")
                print(f"        Note: {avis.get('note_globale', 'N/A')}")
                desc = avis.get('description', 'N/A')
                # Tronquer la description si elle est trop longue
                if len(desc) > 100:
                    desc = desc[:97] + "..."
                print(f"        Description: {desc}")

def analyze_ratings_distribution(avis_collection):
    """Analyser la distribution des notes"""
    print("\n=== ANALYSE DE LA DISTRIBUTION DES NOTES ===")

    # Distribution globale des notes
    pipeline = [
        {"$group": {
            "_id": {"$round": ["$note_globale", 0]},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]

    rating_distribution = list(avis_collection.aggregate(pipeline))

    print("Distribution des notes globales:")
    total = sum(item["count"] for item in rating_distribution)

    for item in rating_distribution:
        note = int(item["_id"]) if item["_id"] is not None else "N/A"
        count = item["count"]
        percentage = (count / total) * 100 if total > 0 else 0
        print(f"  Note {note}: {count} avis ({percentage:.2f}%)")

    # Distribution par catégorie
    categories = [
        ("securite", "Sécurité"),
        ("education", "Éducation"),
        ("sport_loisir", "Sports & Loisirs"),
        ("environnement", "Environnement"),
        ("vie_pratique", "Vie pratique")
    ]

    print("\nMoyenne par catégorie:")
    for field, label in categories:
        pipeline = [
            {"$group": {
                "_id": None,
                "moyenne": {"$avg": f"$notes.{field}"}
            }}
        ]
        result = list(avis_collection.aggregate(pipeline))
        if result:
            moyenne = result[0]["moyenne"]
            print(f"  {label}: {moyenne:.2f}")

    # Répartition géographique des notes (par département)
    pipeline = [
        {"$lookup": {
            "from": "villes",
            "localField": "ville_id",
            "foreignField": "_id",
            "as": "ville"
        }},
        {"$unwind": "$ville"},
        {"$group": {
            "_id": "$ville.department_id",
            "moyenne": {"$avg": "$note_globale"},
            "count": {"$sum": 1}
        }},
        {"$match": {"count": {"$gt": 10}}},  # Au moins 10 avis
        {"$sort": {"moyenne": -1}},
        {"$limit": 10}
    ]

    top_departements = list(avis_collection.aggregate(pipeline))

    print("\nTop 10 des départements les mieux notés:")
    for idx, dept in enumerate(top_departements, 1):
        print(f"{idx}. Département {dept['_id']}: Note moyenne {dept['moyenne']:.2f} ({dept['count']} avis)")

def export_validation_results(villes_collection, avis_collection):
    """Exporter les résultats de validation dans un fichier JSON"""
    results = {
        "date_validation": datetime.now().isoformat(),
        "statistiques": {},
        "completude": {},
        "coherence": {},
        "problemes_potentiels": []
    }

    # Statistiques de base
    results["statistiques"]["total_villes"] = villes_collection.count_documents({})
    results["statistiques"]["total_avis"] = avis_collection.count_documents({})

    # Problèmes de complétude
    villes_sans_avis = villes_collection.count_documents({"nombre_avis": 0})
    results["completude"]["villes_sans_avis"] = villes_sans_avis

    # Incohérences
    pipeline = [
        {"$group": {
            "_id": "$city_id",
            "calculated_avg": {"$avg": "$note_globale"},
            "count": {"$sum": 1}
        }},
        {"$lookup": {
            "from": "villes",
            "localField": "_id",
            "foreignField": "city_id",
            "as": "ville"
        }},
        {"$unwind": {"path": "$ville", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "city_id": "$_id",
            "ville_nom": "$ville.nom",
            "calculated_avg": 1,
            "stored_avg": "$ville.notes.moyenne",
            "difference": {"$abs": {"$subtract": ["$calculated_avg", "$ville.notes.moyenne"]}},
            "count": 1
        }},
        {"$match": {"difference": {"$gt": 0.5}}},
        {"$sort": {"difference": -1}},
        {"$limit": 50}
    ]

    inconsistent_notes = list(avis_collection.aggregate(pipeline))
    results["coherence"]["villes_notes_incoherentes"] = len(inconsistent_notes)

    # Ajouter les problèmes potentiels
    if villes_sans_avis > 0:
        results["problemes_potentiels"].append({
            "type": "villes_sans_avis",
            "description": f"{villes_sans_avis} villes n'ont aucun avis",
            "severite": "moyenne"
        })

    if len(inconsistent_notes) > 0:
        results["problemes_potentiels"].append({
            "type": "notes_incoherentes",
            "description": f"{len(inconsistent_notes)} villes ont des notes moyennes incohérentes",
            "severite": "haute",
            "exemples": [{
                "ville": item.get("ville_nom", "N/A"),
                "city_id": item["city_id"],
                "note_calculee": item["calculated_avg"],
                "note_stockee": item["stored_avg"],
                "ecart": item["difference"]
            } for item in inconsistent_notes[:5]]
        })

    # Enregistrer les résultats dans un fichier
    with open('validation_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\nRésultats de validation exportés dans le fichier 'validation_results.json'")

def main():
    print("Démarrage de la validation des données...")
    client, avis_collection, villes_collection = connect_to_mongodb()

    if not client:
        print("Impossible de se connecter à MongoDB. Arrêt de la validation.")
        return

    try:
        check_basic_statistics(villes_collection, avis_collection)
        check_data_completeness(villes_collection, avis_collection)
        check_data_consistency(villes_collection, avis_collection)
        random_sampling(villes_collection, avis_collection)
        analyze_ratings_distribution(avis_collection)
        export_validation_results(villes_collection, avis_collection)

        print("\nValidation terminée avec succès!")
    except Exception as e:
        logger.error(f"Erreur lors de la validation: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()