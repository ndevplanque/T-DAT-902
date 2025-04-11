#!/usr/bin/env python3
import pymongo
import psycopg2
from datetime import datetime
import logging
import os
from collections import Counter
import time

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/aggregator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

# Connexion à MongoDB
def connect_to_mongodb():
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://root:rootpassword@mongodb:27017/')
    mongo_db = os.environ.get('MONGO_DB', 'villes_france')

    try:
        client = pymongo.MongoClient(mongo_uri)
        db = client[mongo_db]
        logger.info("Connexion à MongoDB réussie")
        return client, db
    except Exception as e:
        logger.error(f"Erreur de connexion à MongoDB: {e}")
        return None, None

# Connexion à PostgreSQL
def connect_to_postgres():
    try:
        conn = psycopg2.connect(
            dbname=os.environ.get('POSTGRES_DB', 'gis_db'),
            user=os.environ.get('POSTGRES_USER', 'postgres'),
            password=os.environ.get('POSTGRES_PASSWORD', 'postgres'),
            host=os.environ.get('POSTGRES_HOST', 'postgres'),
            port=os.environ.get('POSTGRES_PORT', 5432)
        )
        logger.info("Connexion à PostgreSQL réussie")
        return conn
    except Exception as e:
        logger.error(f"Erreur de connexion à PostgreSQL: {e}")
        return None

def wait_for_data_availability(mongo_db, pg_conn, max_retries=12, retry_interval=10):
    """Vérifie que toutes les données nécessaires sont disponibles, attend si nécessaire"""
    logger.info("Vérification de la disponibilité des données...")

    for attempt in range(max_retries):
        mongo_ready = check_mongo_collections(mongo_db)
        postgres_ready = check_postgres_tables(pg_conn)

        if mongo_ready and postgres_ready:
            logger.info("Toutes les données sont disponibles!")
            return True

        logger.warning(f"Certaines données ne sont pas encore disponibles (tentative {attempt+1}/{max_retries})")
        logger.warning(f"MongoDB: {'OK' if mongo_ready else 'PAS PRÊT'}, PostgreSQL: {'OK' if postgres_ready else 'PAS PRÊT'}")

        if attempt < max_retries - 1:
            logger.info(f"Nouvelle tentative dans {retry_interval} secondes...")
            time.sleep(retry_interval)

    logger.error("Données non disponibles après le nombre maximum de tentatives")
    return False

def check_mongo_collections(db):
    """Vérifie que les collections MongoDB nécessaires contiennent des données"""
    try:
        villes_count = db.villes.count_documents({})
        avis_count = db.avis.count_documents({})
        mots_count = db.mots_villes.count_documents({})

        if villes_count > 0 and mots_count > 0:
            logger.info(f"Collections MongoDB prêtes: {villes_count} villes, {avis_count} avis, {mots_count} mots_villes")
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des collections MongoDB: {e}")
        return False

def check_postgres_tables(conn):
    """Vérifie que les tables PostgreSQL nécessaires contiennent des données"""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM departments")
            dept_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM regions")
            region_count = cur.fetchone()[0]

            if dept_count > 0 and region_count > 0:
                logger.info(f"Tables PostgreSQL prêtes: {dept_count} départements, {region_count} régions")
                return True
            else:
                return False
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des tables PostgreSQL: {e}")
        return False

# Charger les mappings département-région depuis PostgreSQL
def load_dept_region_mapping(pg_conn):
    dept_to_region = {}
    regions_info = {}

    try:
        with pg_conn.cursor() as cur:
            # Récupérer le mapping département -> région
            cur.execute("SELECT department_id, region_id FROM departments")
            for row in cur.fetchall():
                dept_to_region[row[0]] = row[1]

            # Récupérer les informations des régions
            cur.execute("SELECT region_id, name FROM regions")
            for row in cur.fetchall():
                regions_info[row[0]] = {"nom": row[1]}

            # Récupérer les informations des départements
            cur.execute("SELECT department_id, name FROM departments")
            departments_info = {row[0]: {"nom": row[1]} for row in cur.fetchall()}

        logger.info(f"Chargement des mappings terminé: {len(dept_to_region)} départements, {len(regions_info)} régions")
        return dept_to_region, regions_info, departments_info
    except Exception as e:
        logger.error(f"Erreur lors du chargement des mappings: {e}")
        return {}, {}, {}

# Fonction pour agréger les données par département
def aggregate_by_department(db, dept_to_region, departments_info):
    logger.info("Début de l'agrégation par département")

    # Pipeline d'agrégation MongoDB pour les statistiques par département
    pipeline = [
        {"$match": {
            "department_id": {"$exists": True, "$ne": ""},
            "nombre_avis": {"$gt": 0}  # N'inclure que les villes avec des avis
        }},
        {"$group": {
            "_id": "$department_id",
            "nombre_villes": {"$sum": 1},
            "nombre_avis": {"$sum": "$nombre_avis"},
            "moyenne_globale": {"$avg": "$notes.moyenne"},
            "moyenne_securite": {"$avg": "$notes.securite"},
            "moyenne_education": {"$avg": "$notes.education"},
            "moyenne_sport_loisir": {"$avg": "$notes.sport_loisir"},
            "moyenne_environnement": {"$avg": "$notes.environnement"},
            "moyenne_vie_pratique": {"$avg": "$notes.vie_pratique"},
            "villes": {"$push": {"nom": "$nom", "city_id": "$city_id"}}
        }}
    ]

    dept_stats = list(db.villes.aggregate(pipeline))

    bulk_ops = []
    for dept in dept_stats:
        dept_id = dept["_id"]
        city_ids = [ville["city_id"] for ville in dept["villes"]]

        # Agréger les sentiments
        sentiment_pipeline = [
            {"$match": {"city_id": {"$in": city_ids}}},
            {"$group": {
                "_id": None,
                "positif": {"$sum": "$sentiments.positif"},
                "neutre": {"$sum": "$sentiments.neutre"},
                "negatif": {"$sum": "$sentiments.negatif"}
            }}
        ]

        sentiment_result = list(db.mots_villes.aggregate(sentiment_pipeline))

        # Agréger les mots fréquents
        mots_pipeline = [
            {"$match": {"city_id": {"$in": city_ids}}},
            {"$unwind": "$mots"},
            {"$group": {
                "_id": "$mots.mot",
                "poids_total": {"$sum": "$mots.poids"}
            }},
            {"$sort": {"poids_total": -1}},
            {"$limit": 50}
        ]

        mots_result = list(db.mots_villes.aggregate(mots_pipeline))
        mots_frequents = [{"mot": item["_id"], "poids": item["poids_total"]} for item in mots_result]

        # Structurer les notes moyennes
        notes = {
            "moyenne": round(dept.pop("moyenne_globale", 0), 1),
            "securite": round(dept.pop("moyenne_securite", 0), 1),
            "education": round(dept.pop("moyenne_education", 0), 1),
            "sport_loisir": round(dept.pop("moyenne_sport_loisir", 0), 1),
            "environnement": round(dept.pop("moyenne_environnement", 0), 1),
            "vie_pratique": round(dept.pop("moyenne_vie_pratique", 0), 1)
        }

        # Calculer les pourcentages de sentiment
        sentiments = {}
        if sentiment_result:
            s = sentiment_result[0]
            total = s["positif"] + s["neutre"] + s["negatif"]
            sentiments = {
                "positif": s["positif"],
                "neutre": s["neutre"],
                "negatif": s["negatif"],
                "positif_percent": round((s["positif"] / total * 100), 1) if total > 0 else 0,
                "neutre_percent": round((s["neutre"] / total * 100), 1) if total > 0 else 0,
                "negatif_percent": round((s["negatif"] / total * 100), 1) if total > 0 else 0
            }

        # Récupérer les métadonnées du département depuis PostgreSQL
        region_id = dept_to_region.get(dept_id, "")
        dept_nom = departments_info.get(dept_id, {}).get("nom", f"Département {dept_id}")

        # Créer le document final
        dept_doc = {
            "_id": dept_id,
            "department_id": dept_id,
            "nom": dept_nom,
            "region_id": region_id,
            "nombre_villes": dept["nombre_villes"],
            "nombre_avis": dept["nombre_avis"],
            "notes": notes,
            "sentiments": sentiments,
            "mots": mots_frequents,
            "date_extraction": datetime.now()
        }

        bulk_ops.append(
            pymongo.UpdateOne(
                {"_id": dept_id},
                {"$set": dept_doc},
                upsert=True
            )
        )

    if bulk_ops:
        result = db.departements_stats.bulk_write(bulk_ops)
        logger.info(f"Agrégation par département terminée: {len(bulk_ops)} départements traités")

    return dept_stats

def aggregate_by_region(db, regions_info):
    logger.info("Début de l'agrégation par région")

    # Utiliser la collection departements_stats pour agréger par région
    pipeline = [
        {"$match": {"region_id": {"$exists": True, "$ne": ""}}},
        {"$group": {
            "_id": "$region_id",
            "departements": {"$push": {"department_id": "$department_id", "nom": "$nom"}},
            "nombre_departements": {"$sum": 1},
            "nombre_villes": {"$sum": "$nombre_villes"},
            "nombre_avis": {"$sum": "$nombre_avis"},
            "mots_freq_depts": {"$push": "$mots"}
        }}
    ]

    region_stats = list(db.departements_stats.aggregate(pipeline))

    bulk_ops = []
    for region in region_stats:
        region_id = region["_id"]
        dept_ids = [dept["department_id"] for dept in region["departements"]]

        # CORRECTIF : Calculer les notes moyennes pondérées par le nombre de villes
        notes_pipeline = [
            {"$match": {"department_id": {"$in": dept_ids}}},
            {"$project": {
                "department_id": 1,
                "notes": 1,
                "nombre_villes": 1  # Inclure le nombre de villes pour la pondération
            }}
        ]

        dept_data = list(db.departements_stats.aggregate(notes_pipeline))

        # Calculer manuellement les moyennes pondérées
        notes = {}
        metrics = ["moyenne", "securite", "education", "sport_loisir", "environnement", "vie_pratique"]

        for metric in metrics:
            values = []
            weights = []

            for dept in dept_data:
                if "notes" in dept and metric in dept["notes"]:
                    values.append(dept["notes"][metric])
                    weights.append(dept["nombre_villes"])  # Pondérer par le nombre de villes

            if values and sum(weights) > 0:
                # Calculer la moyenne pondérée
                weighted_avg = sum(v * w for v, w in zip(values, weights)) / sum(weights)
                notes[metric] = round(weighted_avg, 1)
            else:
                notes[metric] = 0.0

        # Agréger les sentiments
        sentiments_pipeline = [
            {"$match": {"department_id": {"$in": dept_ids}}},
            {"$group": {
                "_id": None,
                "positif": {"$sum": "$sentiments.positif"},
                "neutre": {"$sum": "$sentiments.neutre"},
                "negatif": {"$sum": "$sentiments.negatif"}
            }}
        ]

        sentiment_result = list(db.departements_stats.aggregate(sentiments_pipeline))

        # Calculer les pourcentages de sentiment
        sentiments = {}
        if sentiment_result:
            s = sentiment_result[0]
            total = s["positif"] + s["neutre"] + s["negatif"]
            sentiments = {
                "positif": s["positif"],
                "neutre": s["neutre"],
                "negatif": s["negatif"],
                "positif_percent": round((s["positif"] / total * 100), 1) if total > 0 else 0,
                "neutre_percent": round((s["neutre"] / total * 100), 1) if total > 0 else 0,
                "negatif_percent": round((s["negatif"] / total * 100), 1) if total > 0 else 0
            }

        # Agréger les mots fréquents
        mots_counter = Counter()
        for dept_mots in region.get("mots_freq_depts", []):
            for mot_obj in dept_mots:
                mots_counter[mot_obj["mot"]] += mot_obj["poids"]

        # Convertir en liste triée
        mots_frequents = [{"mot": mot, "poids": poids}
                          for mot, poids in mots_counter.most_common(50)]

        # Récupérer le nom de la région depuis PostgreSQL
        region_nom = regions_info.get(region_id, {}).get("nom", f"Région {region_id}")

        # Créer le document final
        region_doc = {
            "_id": region_id,
            "region_id": region_id,
            "nom": region_nom,
            "nombre_departements": region["nombre_departements"],
            "nombre_villes": region["nombre_villes"],
            "nombre_avis": region["nombre_avis"],
            "notes": notes,
            "sentiments": sentiments,
            "mots": mots_frequents,
            "departements": sorted(region["departements"], key=lambda x: x["department_id"]),
            "date_extraction": datetime.now()
        }

        bulk_ops.append(
            pymongo.UpdateOne(
                {"_id": region_id},
                {"$set": region_doc},
                upsert=True
            )
        )

    if bulk_ops:
        result = db.regions_stats.bulk_write(bulk_ops)
        logger.info(f"Agrégation par région terminée: {len(bulk_ops)} régions traitées")

    return region_stats

# Fonction principale
def main():
    logger.info("Démarrage du processus d'agrégation")

    # Se connecter à MongoDB
    mongo_client, mongo_db = connect_to_mongodb()
    if mongo_client is None or mongo_db is None:
        return

    # Se connecter à PostgreSQL
    pg_conn = connect_to_postgres()
    if pg_conn is None:
        if mongo_client is not None:
            mongo_client.close()
        return

    try:
        # Attendre que toutes les données soient disponibles
        if not wait_for_data_availability(mongo_db, pg_conn):
            logger.error("Impossible de procéder à l'agrégation: données non disponibles")
            return

        # Charger les mappings depuis PostgreSQL
        dept_to_region, regions_info, departments_info = load_dept_region_mapping(pg_conn)

        # Vérifier si les collections existent, sinon les créer
        if "departements_stats" not in mongo_db.list_collection_names():
            mongo_db.create_collection("departements_stats")
            mongo_db.departements_stats.create_index([("department_id", 1)], unique=True)
            mongo_db.departements_stats.create_index([("region_id", 1)])

        if "regions_stats" not in mongo_db.list_collection_names():
            mongo_db.create_collection("regions_stats")
            mongo_db.regions_stats.create_index([("region_id", 1)], unique=True)

        # Effectuer les agrégations
        aggregate_by_department(mongo_db, dept_to_region, departments_info)
        aggregate_by_region(mongo_db, regions_info)

        logger.info("Processus d'agrégation terminé avec succès")

    except Exception as e:
        logger.error(f"Erreur lors du processus d'agrégation: {e}")
    finally:
        # Fermer les connexions
        if mongo_client:
            mongo_client.close()
        if pg_conn:
            pg_conn.close()

if __name__ == "__main__":
    main()