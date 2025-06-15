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

            cur.execute("SELECT COUNT(*) FROM properties")
            properties_count = cur.fetchone()[0]

            if dept_count > 0 and region_count > 0 and properties_count > 0:
                logger.info(f"Tables PostgreSQL prêtes: {dept_count} départements, {region_count} régions, {properties_count} propriétés")
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

# Agrégation des données immobilières
def aggregate_properties_by_city(pg_conn):
    """Calcule les statistiques immobilières par ville
    
    Args:
        pg_conn: Connexion PostgreSQL
    """
    logger.info("Début de l'agrégation des données immobilières par ville")
    
    try:
        with pg_conn.cursor() as cur:
            # Requête d'agrégation complexe pour calculer toutes les statistiques par ville
            query = """
            WITH city_stats AS (
                SELECT 
                    c.city_id,
                    c.name as city_name,
                    c.department_id,
                    c.region_id,
                    COUNT(p.id_mutation) as nb_transactions,
                    COUNT(CASE WHEN p.surface_reelle_bati > 0 THEN 1 END) as nb_transactions_with_surface_bati,
                    COUNT(CASE WHEN p.surface_terrain > 0 THEN 1 END) as nb_transactions_with_surface_terrain,
                    
                    -- Prix statistiques
                    AVG(p.valeur_fonciere) as prix_moyen,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY p.valeur_fonciere) as prix_median,
                    MIN(p.valeur_fonciere) as prix_min,
                    MAX(p.valeur_fonciere) as prix_max,
                    
                    -- Prix au m² (seulement pour les biens avec surface bâti > 0)
                    AVG(CASE WHEN p.surface_reelle_bati > 0 THEN p.valeur_fonciere / p.surface_reelle_bati END) as prix_m2_moyen,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY CASE WHEN p.surface_reelle_bati > 0 THEN p.valeur_fonciere / p.surface_reelle_bati END) as prix_m2_median,
                    
                    -- Surfaces
                    AVG(CASE WHEN p.surface_reelle_bati > 0 THEN p.surface_reelle_bati END) as surface_bati_moyenne,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY CASE WHEN p.surface_reelle_bati > 0 THEN p.surface_reelle_bati END) as surface_bati_mediane,
                    AVG(CASE WHEN p.surface_terrain > 0 THEN p.surface_terrain END) as surface_terrain_moyenne,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY CASE WHEN p.surface_terrain > 0 THEN p.surface_terrain END) as surface_terrain_mediane,
                    
                    -- Périodes temporelles
                    MIN(p.date_mutation) as premiere_transaction,
                    MAX(p.date_mutation) as derniere_transaction,
                    
                    -- Calcul de la densité (transactions / surface en km²)
                    COUNT(p.id_mutation) / NULLIF((ST_Area(ST_Transform(c.geom, 3857)) / 1000000.0), 0) as densite_transactions_km2
                    
                FROM cities c
                LEFT JOIN properties p ON c.city_id = p.code_commune
                WHERE p.valeur_fonciere > 0  -- Exclure les transactions sans valeur
                GROUP BY c.city_id, c.name, c.department_id, c.region_id, c.geom
                HAVING COUNT(p.id_mutation) > 0  -- Seulement les villes avec des transactions
            )
            INSERT INTO properties_cities_stats (
                city_id, city_name, department_id, region_id,
                nb_transactions, nb_transactions_with_surface_bati, nb_transactions_with_surface_terrain,
                prix_moyen, prix_median, prix_min, prix_max, prix_m2_moyen, prix_m2_median,
                surface_bati_moyenne, surface_bati_mediane, surface_terrain_moyenne, surface_terrain_mediane,
                premiere_transaction, derniere_transaction, densite_transactions_km2
            )
            SELECT 
                city_id, city_name, department_id, region_id,
                nb_transactions, nb_transactions_with_surface_bati, nb_transactions_with_surface_terrain,
                ROUND(prix_moyen::numeric, 2), ROUND(prix_median::numeric, 2), 
                ROUND(prix_min::numeric, 2), ROUND(prix_max::numeric, 2),
                ROUND(prix_m2_moyen::numeric, 2), ROUND(prix_m2_median::numeric, 2),
                ROUND(surface_bati_moyenne::numeric, 2), ROUND(surface_bati_mediane::numeric, 2),
                ROUND(surface_terrain_moyenne::numeric, 2), ROUND(surface_terrain_mediane::numeric, 2),
                premiere_transaction, derniere_transaction, ROUND(densite_transactions_km2::numeric, 4)
            FROM city_stats
            ON CONFLICT (city_id) DO UPDATE SET
                city_name = EXCLUDED.city_name,
                department_id = EXCLUDED.department_id,
                region_id = EXCLUDED.region_id,
                nb_transactions = EXCLUDED.nb_transactions,
                nb_transactions_with_surface_bati = EXCLUDED.nb_transactions_with_surface_bati,
                nb_transactions_with_surface_terrain = EXCLUDED.nb_transactions_with_surface_terrain,
                prix_moyen = EXCLUDED.prix_moyen,
                prix_median = EXCLUDED.prix_median,
                prix_min = EXCLUDED.prix_min,
                prix_max = EXCLUDED.prix_max,
                prix_m2_moyen = EXCLUDED.prix_m2_moyen,
                prix_m2_median = EXCLUDED.prix_m2_median,
                surface_bati_moyenne = EXCLUDED.surface_bati_moyenne,
                surface_bati_mediane = EXCLUDED.surface_bati_mediane,
                surface_terrain_moyenne = EXCLUDED.surface_terrain_moyenne,
                surface_terrain_mediane = EXCLUDED.surface_terrain_mediane,
                premiere_transaction = EXCLUDED.premiere_transaction,
                derniere_transaction = EXCLUDED.derniere_transaction,
                densite_transactions_km2 = EXCLUDED.densite_transactions_km2,
                date_extraction = CURRENT_TIMESTAMP;
            """
            
            cur.execute(query)
            affected_rows = cur.rowcount
            logger.info(f"Query executed, affected rows: {affected_rows}")
            
            # Vérifier le nombre de lignes dans la table
            cur.execute("SELECT COUNT(*) FROM properties_cities_stats")
            count_result = cur.fetchone()
            logger.info(f"Agrégation par ville terminée: {count_result[0]} villes dans la table")
            
    except Exception as e:
        logger.error(f"Erreur lors de l'agrégation immobilière par ville: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def aggregate_properties_by_department(pg_conn):
    """Calcule les statistiques immobilières par département
    
    Args:
        pg_conn: Connexion PostgreSQL
    """
    logger.info("Début de l'agrégation des données immobilières par département")
    
    try:
        with pg_conn.cursor() as cur:
            # Agrégation basée sur les statistiques par ville
            query = """
            WITH dept_stats AS (
                SELECT 
                    d.department_id,
                    d.name as department_name,
                    d.region_id,
                    COUNT(pcs.city_id) as nb_villes_avec_transactions,
                    SUM(pcs.nb_transactions) as nb_transactions_total,
                    SUM(pcs.nb_transactions_with_surface_bati) as nb_transactions_with_surface_bati,
                    SUM(pcs.nb_transactions_with_surface_terrain) as nb_transactions_with_surface_terrain,
                    
                    -- Moyennes pondérées par le nombre de transactions
                    SUM(pcs.prix_moyen * pcs.nb_transactions) / NULLIF(SUM(pcs.nb_transactions), 0) as prix_moyen,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pcs.prix_median) as prix_median,
                    MIN(pcs.prix_min) as prix_min,
                    MAX(pcs.prix_max) as prix_max,
                    
                    -- Prix au m² pondérés
                    SUM(CASE WHEN pcs.prix_m2_moyen IS NOT NULL AND pcs.nb_transactions_with_surface_bati > 0 
                        THEN pcs.prix_m2_moyen * pcs.nb_transactions_with_surface_bati END) / 
                    NULLIF(SUM(CASE WHEN pcs.nb_transactions_with_surface_bati > 0 THEN pcs.nb_transactions_with_surface_bati END), 0) as prix_m2_moyen,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pcs.prix_m2_median) as prix_m2_median,
                    
                    -- Surfaces pondérées
                    SUM(CASE WHEN pcs.surface_bati_moyenne IS NOT NULL AND pcs.nb_transactions_with_surface_bati > 0 
                        THEN pcs.surface_bati_moyenne * pcs.nb_transactions_with_surface_bati END) / 
                    NULLIF(SUM(CASE WHEN pcs.nb_transactions_with_surface_bati > 0 THEN pcs.nb_transactions_with_surface_bati END), 0) as surface_bati_moyenne,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pcs.surface_bati_mediane) as surface_bati_mediane,
                    SUM(CASE WHEN pcs.surface_terrain_moyenne IS NOT NULL AND pcs.nb_transactions_with_surface_terrain > 0 
                        THEN pcs.surface_terrain_moyenne * pcs.nb_transactions_with_surface_terrain END) / 
                    NULLIF(SUM(CASE WHEN pcs.nb_transactions_with_surface_terrain > 0 THEN pcs.nb_transactions_with_surface_terrain END), 0) as surface_terrain_moyenne,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pcs.surface_terrain_mediane) as surface_terrain_mediane,
                    
                    -- Périodes temporelles
                    MIN(pcs.premiere_transaction) as premiere_transaction,
                    MAX(pcs.derniere_transaction) as derniere_transaction,
                    
                    -- Densité moyenne pondérée
                    SUM(pcs.densite_transactions_km2 * pcs.nb_transactions) / NULLIF(SUM(pcs.nb_transactions), 0) as densite_transactions_km2
                    
                FROM departments d
                LEFT JOIN properties_cities_stats pcs ON d.department_id = pcs.department_id
                WHERE pcs.nb_transactions > 0
                GROUP BY d.department_id, d.name, d.region_id
                HAVING COUNT(pcs.city_id) > 0
            )
            INSERT INTO properties_departments_stats (
                department_id, department_name, region_id,
                nb_villes_avec_transactions, nb_transactions_total, nb_transactions_with_surface_bati, nb_transactions_with_surface_terrain,
                prix_moyen, prix_median, prix_min, prix_max, prix_m2_moyen, prix_m2_median,
                surface_bati_moyenne, surface_bati_mediane, surface_terrain_moyenne, surface_terrain_mediane,
                premiere_transaction, derniere_transaction, densite_transactions_km2
            )
            SELECT 
                department_id, department_name, region_id,
                nb_villes_avec_transactions, nb_transactions_total, nb_transactions_with_surface_bati, nb_transactions_with_surface_terrain,
                ROUND(prix_moyen::numeric, 2), ROUND(prix_median::numeric, 2), 
                ROUND(prix_min::numeric, 2), ROUND(prix_max::numeric, 2),
                ROUND(prix_m2_moyen::numeric, 2), ROUND(prix_m2_median::numeric, 2),
                ROUND(surface_bati_moyenne::numeric, 2), ROUND(surface_bati_mediane::numeric, 2),
                ROUND(surface_terrain_moyenne::numeric, 2), ROUND(surface_terrain_mediane::numeric, 2),
                premiere_transaction, derniere_transaction, ROUND(densite_transactions_km2::numeric, 4)
            FROM dept_stats
            ON CONFLICT (department_id) DO UPDATE SET
                department_name = EXCLUDED.department_name,
                region_id = EXCLUDED.region_id,
                nb_villes_avec_transactions = EXCLUDED.nb_villes_avec_transactions,
                nb_transactions_total = EXCLUDED.nb_transactions_total,
                nb_transactions_with_surface_bati = EXCLUDED.nb_transactions_with_surface_bati,
                nb_transactions_with_surface_terrain = EXCLUDED.nb_transactions_with_surface_terrain,
                prix_moyen = EXCLUDED.prix_moyen,
                prix_median = EXCLUDED.prix_median,
                prix_min = EXCLUDED.prix_min,
                prix_max = EXCLUDED.prix_max,
                prix_m2_moyen = EXCLUDED.prix_m2_moyen,
                prix_m2_median = EXCLUDED.prix_m2_median,
                surface_bati_moyenne = EXCLUDED.surface_bati_moyenne,
                surface_bati_mediane = EXCLUDED.surface_bati_mediane,
                surface_terrain_moyenne = EXCLUDED.surface_terrain_moyenne,
                surface_terrain_mediane = EXCLUDED.surface_terrain_mediane,
                premiere_transaction = EXCLUDED.premiere_transaction,
                derniere_transaction = EXCLUDED.derniere_transaction,
                densite_transactions_km2 = EXCLUDED.densite_transactions_km2,
                date_extraction = CURRENT_TIMESTAMP;
            """
            
            cur.execute(query)
            affected_rows = cur.rowcount
            logger.info(f"Agrégation par département terminée: {affected_rows} départements traités")
            
    except Exception as e:
        logger.error(f"Erreur lors de l'agrégation immobilière par département: {e}")
        raise

def aggregate_properties_by_region(pg_conn):
    """Calcule les statistiques immobilières par région
    
    Args:
        pg_conn: Connexion PostgreSQL
    """
    logger.info("Début de l'agrégation des données immobilières par région")
    
    try:
        with pg_conn.cursor() as cur:
            # Agrégation basée sur les statistiques par département
            query = """
            WITH region_stats AS (
                SELECT 
                    r.region_id,
                    r.name as region_name,
                    COUNT(pds.department_id) as nb_departements_avec_transactions,
                    SUM(pds.nb_villes_avec_transactions) as nb_villes_avec_transactions,
                    SUM(pds.nb_transactions_total) as nb_transactions_total,
                    SUM(pds.nb_transactions_with_surface_bati) as nb_transactions_with_surface_bati,
                    SUM(pds.nb_transactions_with_surface_terrain) as nb_transactions_with_surface_terrain,
                    
                    -- Moyennes pondérées par le nombre de transactions
                    SUM(pds.prix_moyen * pds.nb_transactions_total) / NULLIF(SUM(pds.nb_transactions_total), 0) as prix_moyen,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pds.prix_median) as prix_median,
                    MIN(pds.prix_min) as prix_min,
                    MAX(pds.prix_max) as prix_max,
                    
                    -- Prix au m² pondérés
                    SUM(CASE WHEN pds.prix_m2_moyen IS NOT NULL AND pds.nb_transactions_with_surface_bati > 0 
                        THEN pds.prix_m2_moyen * pds.nb_transactions_with_surface_bati END) / 
                    NULLIF(SUM(CASE WHEN pds.nb_transactions_with_surface_bati > 0 THEN pds.nb_transactions_with_surface_bati END), 0) as prix_m2_moyen,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pds.prix_m2_median) as prix_m2_median,
                    
                    -- Surfaces pondérées
                    SUM(CASE WHEN pds.surface_bati_moyenne IS NOT NULL AND pds.nb_transactions_with_surface_bati > 0 
                        THEN pds.surface_bati_moyenne * pds.nb_transactions_with_surface_bati END) / 
                    NULLIF(SUM(CASE WHEN pds.nb_transactions_with_surface_bati > 0 THEN pds.nb_transactions_with_surface_bati END), 0) as surface_bati_moyenne,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pds.surface_bati_mediane) as surface_bati_mediane,
                    SUM(CASE WHEN pds.surface_terrain_moyenne IS NOT NULL AND pds.nb_transactions_with_surface_terrain > 0 
                        THEN pds.surface_terrain_moyenne * pds.nb_transactions_with_surface_terrain END) / 
                    NULLIF(SUM(CASE WHEN pds.nb_transactions_with_surface_terrain > 0 THEN pds.nb_transactions_with_surface_terrain END), 0) as surface_terrain_moyenne,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pds.surface_terrain_mediane) as surface_terrain_mediane,
                    
                    -- Périodes temporelles
                    MIN(pds.premiere_transaction) as premiere_transaction,
                    MAX(pds.derniere_transaction) as derniere_transaction,
                    
                    -- Densité moyenne pondérée
                    SUM(pds.densite_transactions_km2 * pds.nb_transactions_total) / NULLIF(SUM(pds.nb_transactions_total), 0) as densite_transactions_km2
                    
                FROM regions r
                LEFT JOIN properties_departments_stats pds ON r.region_id = pds.region_id
                WHERE pds.nb_transactions_total > 0
                GROUP BY r.region_id, r.name
                HAVING COUNT(pds.department_id) > 0
            )
            INSERT INTO properties_regions_stats (
                region_id, region_name,
                nb_departements_avec_transactions, nb_villes_avec_transactions, nb_transactions_total, 
                nb_transactions_with_surface_bati, nb_transactions_with_surface_terrain,
                prix_moyen, prix_median, prix_min, prix_max, prix_m2_moyen, prix_m2_median,
                surface_bati_moyenne, surface_bati_mediane, surface_terrain_moyenne, surface_terrain_mediane,
                premiere_transaction, derniere_transaction, densite_transactions_km2
            )
            SELECT 
                region_id, region_name,
                nb_departements_avec_transactions, nb_villes_avec_transactions, nb_transactions_total,
                nb_transactions_with_surface_bati, nb_transactions_with_surface_terrain,
                ROUND(prix_moyen::numeric, 2), ROUND(prix_median::numeric, 2), 
                ROUND(prix_min::numeric, 2), ROUND(prix_max::numeric, 2),
                ROUND(prix_m2_moyen::numeric, 2), ROUND(prix_m2_median::numeric, 2),
                ROUND(surface_bati_moyenne::numeric, 2), ROUND(surface_bati_mediane::numeric, 2),
                ROUND(surface_terrain_moyenne::numeric, 2), ROUND(surface_terrain_mediane::numeric, 2),
                premiere_transaction, derniere_transaction, ROUND(densite_transactions_km2::numeric, 4)
            FROM region_stats
            ON CONFLICT (region_id) DO UPDATE SET
                region_name = EXCLUDED.region_name,
                nb_departements_avec_transactions = EXCLUDED.nb_departements_avec_transactions,
                nb_villes_avec_transactions = EXCLUDED.nb_villes_avec_transactions,
                nb_transactions_total = EXCLUDED.nb_transactions_total,
                nb_transactions_with_surface_bati = EXCLUDED.nb_transactions_with_surface_bati,
                nb_transactions_with_surface_terrain = EXCLUDED.nb_transactions_with_surface_terrain,
                prix_moyen = EXCLUDED.prix_moyen,
                prix_median = EXCLUDED.prix_median,
                prix_min = EXCLUDED.prix_min,
                prix_max = EXCLUDED.prix_max,
                prix_m2_moyen = EXCLUDED.prix_m2_moyen,
                prix_m2_median = EXCLUDED.prix_m2_median,
                surface_bati_moyenne = EXCLUDED.surface_bati_moyenne,
                surface_bati_mediane = EXCLUDED.surface_bati_mediane,
                surface_terrain_moyenne = EXCLUDED.surface_terrain_moyenne,
                surface_terrain_mediane = EXCLUDED.surface_terrain_mediane,
                premiere_transaction = EXCLUDED.premiere_transaction,
                derniere_transaction = EXCLUDED.derniere_transaction,
                densite_transactions_km2 = EXCLUDED.densite_transactions_km2,
                date_extraction = CURRENT_TIMESTAMP;
            """
            
            cur.execute(query)
            affected_rows = cur.rowcount
            logger.info(f"Agrégation par région terminée: {affected_rows} régions traitées")
            
    except Exception as e:
        logger.error(f"Erreur lors de l'agrégation immobilière par région: {e}")
        raise

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

        # Effectuer les agrégations MongoDB (avis et sentiments)
        aggregate_by_department(mongo_db, dept_to_region, departments_info)
        aggregate_by_region(mongo_db, regions_info)

        # Effectuer les agrégations PostgreSQL (données immobilières)
        logger.info("Début des agrégations immobilières")
        aggregate_properties_by_city(pg_conn)
        pg_conn.commit()
        logger.info("Agrégation immobilière par ville terminée")
        aggregate_properties_by_department(pg_conn)
        pg_conn.commit()
        logger.info("Agrégation immobilière par département terminée")
        aggregate_properties_by_region(pg_conn)
        pg_conn.commit()
        logger.info("Agrégation immobilière par région terminée")

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