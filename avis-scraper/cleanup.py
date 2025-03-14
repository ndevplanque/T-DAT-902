#!/usr/bin/env python3
import pymongo
import logging
import os
import re
from datetime import datetime

# Configuration du logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/cleanup.log"),
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
        # Ping pour vérifier la connexion
        client.admin.command('ping')
        logger.info("Connexion à MongoDB réussie")

        db = client[mongo_db]
        avis_collection = db["avis"]
        villes_collection = db["villes"]

        return client, avis_collection, villes_collection
    except Exception as e:
        logger.error(f"Erreur de connexion à MongoDB: {e}")
        return None, None, None

def identify_invalid_entries(villes_collection):
    """
    Identifie les entrées qui ne respectent pas le format d'URL attendu:
    https://www.bien-dans-ma-ville.fr/nom-numéro/avis.html
    """
    # Pattern pour valider les URLs (nom-numéro/avis.html)
    valid_pattern = re.compile(r'https://www\.bien-dans-ma-ville\.fr/[^/]+-\d+/avis\.html$')

    # Récupérer toutes les villes
    all_entries = list(villes_collection.find({}, {"_id": 1, "url": 1, "nom": 1}))

    # Filtrer les entrées invalides
    invalid_entries = [entry for entry in all_entries if not valid_pattern.match(entry.get("url", ""))]

    logger.info(f"Total des entrées dans la collection: {len(all_entries)}")
    logger.info(f"Entrées invalides identifiées: {len(invalid_entries)}")

    return invalid_entries

def cleanup_invalid_entries(villes_collection, avis_collection, dry_run=True):
    """
    Nettoie les entrées invalides et leurs avis associés de la base de données.
    Mode dry_run: affiche simplement les actions qui seraient entreprises sans les exécuter.
    """
    # Identifier les entrées invalides
    invalid_entries = identify_invalid_entries(villes_collection)
    invalid_ids = [entry["_id"] for entry in invalid_entries]

    if not invalid_entries:
        logger.info("Aucune entrée invalide trouvée. Rien à nettoyer.")
        return 0, 0

    # Créer un fichier de sauvegarde des entrées à supprimer (pour référence)
    backup_file = f"invalid_entries_to_remove_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(backup_file, "w") as f:
        for entry in invalid_entries:
            f.write(f"{entry['_id']} - {entry.get('nom', 'N/A')} - {entry.get('url', 'N/A')}\n")

    logger.info(f"Liste des entrées à supprimer sauvegardée dans {backup_file}")

    # Compter les avis associés à ces entrées
    avis_count = avis_collection.count_documents({"ville_id": {"$in": invalid_ids}})
    logger.info(f"Trouvé {avis_count} avis associés aux entrées invalides")

    if dry_run:
        logger.info(f"[DRY RUN] {len(invalid_entries)} entrées invalides et {avis_count} avis seraient supprimés")
        return len(invalid_entries), avis_count

    # Supprimer les avis des entrées invalides
    avis_result = avis_collection.delete_many({"ville_id": {"$in": invalid_ids}})
    logger.info(f"Supprimé {avis_result.deleted_count} avis d'entrées invalides")

    # Supprimer les entrées invalides
    villes_result = villes_collection.delete_many({"_id": {"$in": invalid_ids}})
    logger.info(f"Supprimé {villes_result.deleted_count} entrées invalides")

    return villes_result.deleted_count, avis_result.deleted_count

def analyze_invalid_entries(villes_collection):
    """
    Analyse les types d'entrées invalides pour mieux comprendre leur origine
    """
    # Pattern pour valider les URLs
    valid_pattern = re.compile(r'https://www\.bien-dans-ma-ville\.fr/[^/]+-\d+/avis\.html$')

    # Récupérer toutes les URLs
    all_urls = [doc.get("url", "") for doc in villes_collection.find({}, {"url": 1})]

    # Catégoriser les URLs
    categories = {
        "valides": [],
        "quartiers": [],
        "arrondissements": [],
        "autres": []
    }

    for url in all_urls:
        if valid_pattern.match(url):
            categories["valides"].append(url)
        elif "/quartier-" in url:
            categories["quartiers"].append(url)
        elif "arrondissement" in url.lower():
            categories["arrondissements"].append(url)
        else:
            categories["autres"].append(url)

    # Afficher les résultats de l'analyse
    logger.info("=== ANALYSE DES TYPES D'ENTRÉES ===")
    logger.info(f"Total des URLs: {len(all_urls)}")
    logger.info(f"URLs valides: {len(categories['valides'])}")
    logger.info(f"URLs de quartiers: {len(categories['quartiers'])}")
    logger.info(f"URLs d'arrondissements: {len(categories['arrondissements'])}")
    logger.info(f"Autres URLs invalides: {len(categories['autres'])}")

    # Afficher quelques exemples de chaque catégorie
    if categories["quartiers"]:
        logger.info(f"Exemple de quartier: {categories['quartiers'][0]}")
    if categories["arrondissements"]:
        logger.info(f"Exemple d'arrondissement: {categories['arrondissements'][0]}")
    if categories["autres"]:
        logger.info(f"Exemple d'autre URL invalide: {categories['autres'][0]}")

def main():
    """Fonction principale du script de nettoyage"""
    logger.info("=== DÉBUT DU NETTOYAGE DES ENTRÉES INVALIDES ===")

    # Se connecter à MongoDB
    client, avis_collection, villes_collection = connect_to_mongodb()
    if not client:
        logger.error("Impossible de se connecter à la base de données")
        return

    try:
        # Analyser les types d'entrées
        analyze_invalid_entries(villes_collection)

        # D'abord exécuter en dry_run pour voir ce qui serait supprimé
        invalid_count, avis_count = cleanup_invalid_entries(villes_collection, avis_collection, dry_run=True)

        # Demander confirmation
        if invalid_count > 0:
            print(f"\n{invalid_count} entrées invalides et {avis_count} avis seraient supprimés.")
            confirm = input("Voulez-vous continuer avec la suppression réelle ? (y/n): ")

            if confirm.lower() == 'y':
                # Exécuter la suppression réelle
                deleted_entries, deleted_avis = cleanup_invalid_entries(villes_collection, avis_collection, dry_run=False)
                logger.info(f"Nettoyage terminé: {deleted_entries} entrées invalides et {deleted_avis} avis supprimés")
            else:
                logger.info("Opération annulée par l'utilisateur")
        else:
            logger.info("Aucune entrée invalide trouvée à supprimer")

    except Exception as e:
        logger.error(f"Erreur lors du nettoyage: {e}")
    finally:
        client.close()

    logger.info("=== FIN DU NETTOYAGE DES ENTRÉES INVALIDES ===")

if __name__ == "__main__":
    main()