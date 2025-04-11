#!/usr/bin/env python3
import pymongo
import psycopg2
import json
import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import time
from collections import Counter
import sys

# Configuration du logging
# Nous allons configurer le logging une fois que nous connaissons le répertoire de sortie
logger = logging.getLogger()

def setup_logging():
    """Configure le logging avec les handlers appropriés"""
    output_dir = os.environ.get('OUTPUT_DIR', 'results')

    # Si le répertoire n'existe pas, créons-le
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except Exception as e:
            print(f"Erreur lors de la création du répertoire {output_dir}: {e}")
            output_dir = "/tmp"
            print(f"Utilisation du répertoire temporaire: {output_dir}")

    # Vérifier si on peut écrire dans ce répertoire
    log_file = os.path.join(output_dir, "validation.log")
    try:
        with open(log_file, "a") as f:
            f.write("Test d'écriture du log\n")
    except Exception as e:
        print(f"Impossible d'écrire dans le fichier de log {log_file}: {e}")
        log_file = "/tmp/validation.log"
        print(f"Utilisation du fichier de log: {log_file}")

    # Configurer le logging avec le fichier de log et la console
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    return output_dir

# Appeler setup_logging au démarrage du script
try:
    output_dir = setup_logging()
    logger.info(f"Logging configuré avec succès. Fichier de log: {os.path.join(output_dir, 'validation.log')}")
except Exception as e:
    # Configurer un logging de secours si setup_logging échoue
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    logger.error(f"Erreur lors de la configuration du logging: {e}")
    logger.info("Utilisation du logging de secours (console uniquement)")

def connect_to_mongodb():
    """Établit une connexion à MongoDB"""
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://root:rootpassword@mongodb:27017/')
    mongo_db_name = os.environ.get('MONGO_DB', 'villes_france')

    try:
        logger.info(f"Tentative de connexion à MongoDB: {mongo_uri}, DB: {mongo_db_name}")
        client = pymongo.MongoClient(mongo_uri)
        # Tester la connexion
        client.admin.command('ping')
        logger.info("Ping MongoDB réussi")

        # Obtenir la base de données
        db = client[mongo_db_name]
        logger.info(f"Connexion à MongoDB réussie, base de données: {mongo_db_name}")
        return client, db
    except Exception as e:
        logger.error(f"Erreur de connexion à MongoDB: {str(e)}")
        return None, None

def connect_to_postgres():
    """Établit une connexion à PostgreSQL"""
    try:
        logger.info("Tentative de connexion à PostgreSQL...")
        db = os.environ.get('POSTGRES_DB', 'gis_db')
        user = os.environ.get('POSTGRES_USER', 'postgres')
        password = os.environ.get('POSTGRES_PASSWORD', 'postgres')
        host = os.environ.get('POSTGRES_HOST', 'postgres')
        port = os.environ.get('POSTGRES_PORT', 5432)

        logger.info(f"Paramètres de connexion PostgreSQL: host={host}, port={port}, dbname={db}, user={user}")

        conn = psycopg2.connect(
            dbname=db,
            user=user,
            password=password,
            host=host,
            port=port
        )
        logger.info("Connexion à PostgreSQL réussie")
        return conn
    except Exception as e:
        logger.error(f"Erreur de connexion à PostgreSQL: {str(e)}")
        return None

def wait_for_collections(db, collections, max_retries=10, retry_interval=5):
    """Attend que les collections soient disponibles"""
    for retry in range(max_retries):
        try:
            available_collections = db.list_collection_names()
            logger.info(f"Collections disponibles: {available_collections}")

            # Vérifier quelles collections sont manquantes
            missing = [coll for coll in collections if coll not in available_collections]

            if not missing:
                logger.info(f"Toutes les collections sont disponibles: {collections}")

                # Vérifier également que les collections contiennent des données
                non_empty_colls = []
                for coll in collections:
                    count = db[coll].count_documents({}, limit=1)
                    non_empty_colls.append(f"{coll}({count})")
                    if count == 0:
                        logger.warning(f"La collection {coll} est vide")

                logger.info(f"Collections non vides: {non_empty_colls}")

                # Si toutes les collections requises existent, nous considérons que c'est suffisant,
                # même si certaines sont vides, car nous gérerons ce cas plus tard
                return True

            logger.warning(f"Collections manquantes: {missing}. Tentative {retry+1}/{max_retries}")
            time.sleep(retry_interval)

        except Exception as e:
            logger.error(f"Erreur lors de la vérification des collections: {str(e)}")
            time.sleep(retry_interval)

    logger.error(f"Impossible de trouver toutes les collections requises après {max_retries} tentatives")
    # Lister les collections disponibles et manquantes une dernière fois
    try:
        available = db.list_collection_names()
        missing = [coll for coll in collections if coll not in available]
        logger.error(f"Collections disponibles: {available}")
        logger.error(f"Collections manquantes: {missing}")
    except Exception as e:
        logger.error(f"Impossible de lister les collections: {str(e)}")

    return False

def check_collection_stats(db):
    """Vérifie les statistiques de base des collections"""
    results = {
        "villes": db.villes.count_documents({}),
        "avis": db.avis.count_documents({}),
        "mots_villes": db.mots_villes.count_documents({}),
        "departements_stats": db.departements_stats.count_documents({}),
        "regions_stats": db.regions_stats.count_documents({})
    }

    logger.info(f"Statistiques des collections:")
    for coll, count in results.items():
        logger.info(f"  - {coll}: {count} documents")

    # Vérifier si les données semblent cohérentes
    validation_results = {}
    validation_results["villes_has_data"] = results["villes"] > 0
    validation_results["has_aggregated_departments"] = results["departements_stats"] > 0
    validation_results["has_aggregated_regions"] = results["regions_stats"] > 0

    # Vérifier si le nombre de départements et régions semble cohérent pour la France
    validation_results["dept_count_reasonable"] = 90 <= results["departements_stats"] <= 110
    validation_results["region_count_reasonable"] = 12 <= results["regions_stats"] <= 18

    return results, validation_results

def validate_department_aggregations(db, pg_conn):
    """Valide les agrégations par département"""
    # 1. Compter les départements dans PostgreSQL
    pg_dept_count = 0
    with pg_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM departments")
        pg_dept_count = cur.fetchone()[0]

    # 2. Compter les départements agrégés dans MongoDB
    mongo_dept_count = db.departements_stats.count_documents({})

    # 3. Vérifier la cohérence
    count_match = mongo_dept_count == pg_dept_count
    logger.info(f"Validation des départements: MongoDB={mongo_dept_count}, PostgreSQL={pg_dept_count}, Cohérent={count_match}")

    # 4. Vérifier la structure d'un échantillon
    sample = db.departements_stats.find_one({})
    structure_valid = False
    if sample:
        required_fields = ["_id", "department_id", "nom", "region_id", "nombre_villes",
                           "nombre_avis", "notes", "sentiments", "mots"]
        structure_valid = all(field in sample for field in required_fields)

        if structure_valid:
            # Vérifier la structure des sous-champs
            structure_valid = (
                    isinstance(sample["notes"], dict) and
                    isinstance(sample["sentiments"], dict) and
                    isinstance(sample["mots"], list)
            )

    logger.info(f"Structure des départements valide: {structure_valid}")

    # 5. Vérifier le référencement des régions
    dept_to_region_consistency = True
    with pg_conn.cursor() as cur:
        cur.execute("SELECT department_id, region_id FROM departments")
        pg_mapping = {row[0]: row[1] for row in cur.fetchall()}

        # Vérifier si les départements font référence aux bonnes régions
        for dept in db.departements_stats.find({}, {"department_id": 1, "region_id": 1}):
            dept_id = dept["department_id"]
            if dept_id in pg_mapping and dept["region_id"] != pg_mapping[dept_id]:
                logger.error(f"Incohérence région pour département {dept_id}: MongoDB={dept['region_id']}, PostgreSQL={pg_mapping[dept_id]}")
                dept_to_region_consistency = False

    logger.info(f"Cohérence département-région: {dept_to_region_consistency}")

    return {
        "count_match": count_match,
        "structure_valid": structure_valid,
        "dept_to_region_consistency": dept_to_region_consistency
    }

def validate_region_aggregations(db, pg_conn):
    """Valide les agrégations par région"""
    # 1. Compter les régions dans PostgreSQL
    pg_region_count = 0
    with pg_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM regions")
        pg_region_count = cur.fetchone()[0]

    # 2. Compter les régions agrégées dans MongoDB
    mongo_region_count = db.regions_stats.count_documents({})

    # 3. Vérifier la cohérence
    count_match = mongo_region_count == pg_region_count
    logger.info(f"Validation des régions: MongoDB={mongo_region_count}, PostgreSQL={pg_region_count}, Cohérent={count_match}")

    # 4. Vérifier la structure d'un échantillon
    sample = db.regions_stats.find_one({})
    structure_valid = False
    if sample:
        required_fields = ["_id", "region_id", "nom", "nombre_departements", "nombre_villes",
                           "nombre_avis", "notes", "sentiments", "mots", "departements"]
        structure_valid = all(field in sample for field in required_fields)

        if structure_valid:
            # Vérifier la structure des sous-champs
            structure_valid = (
                    isinstance(sample["notes"], dict) and
                    isinstance(sample["sentiments"], dict) and
                    isinstance(sample["mots"], list) and
                    isinstance(sample["departements"], list)
            )

    logger.info(f"Structure des régions valide: {structure_valid}")

    # 5. Vérifier la cohérence des départements dans les régions
    dept_count_consistency = True
    region_samples = list(db.regions_stats.find({}, {"region_id": 1, "departements": 1, "nombre_departements": 1}))

    for region in region_samples:
        if len(region["departements"]) != region["nombre_departements"]:
            logger.error(f"Incohérence pour région {region['region_id']}: nombre_departements={region['nombre_departements']}, mais liste contient {len(region['departements'])} départements")
            dept_count_consistency = False

    logger.info(f"Cohérence du nombre de départements dans les régions: {dept_count_consistency}")

    return {
        "count_match": count_match,
        "structure_valid": structure_valid,
        "dept_count_consistency": dept_count_consistency
    }

def validate_notes_agregation(db):
    """Valide les calculs d'agrégation des notes"""
    validation_results = {}

    # 1. Vérifier que toutes les notes sont entre 0 et 10
    notes_range_dept = db.departements_stats.find_one(
        {"notes.moyenne": {"$not": {"$gte": 0, "$lte": 10}}}
    )

    notes_range_region = db.regions_stats.find_one(
        {"notes.moyenne": {"$not": {"$gte": 0, "$lte": 10}}}
    )

    validation_results["notes_in_range_dept"] = notes_range_dept is None
    validation_results["notes_in_range_region"] = notes_range_region is None

    if not validation_results["notes_in_range_dept"]:
        logger.error(f"Des notes de département sont hors limites: {notes_range_dept['_id']}")
    if not validation_results["notes_in_range_region"]:
        logger.error(f"Des notes de région sont hors limites: {notes_range_region['_id']}")

    # 2. Vérifier la cohérence des sentiments (somme des pourcentages = 100%)
    sentiments_sum_dept = db.departements_stats.find_one({
        "$expr": {
            "$ne": [
                {"$round": [{"$add": ["$sentiments.positif_percent", "$sentiments.neutre_percent", "$sentiments.negatif_percent"]}, 0]},
                100
            ]
        },
        "sentiments.positif": {"$gt": 0}  # Pour éviter les cas où il n'y a pas de sentiments
    })

    validation_results["sentiments_percents_valid_dept"] = sentiments_sum_dept is None

    if not validation_results["sentiments_percents_valid_dept"]:
        logger.error(f"Des pourcentages de sentiments départementaux ne totalisent pas 100%: {sentiments_sum_dept['_id']}")

    # Mêmes vérifications pour les régions
    sentiments_sum_region = db.regions_stats.find_one({
        "$expr": {
            "$ne": [
                {"$round": [{"$add": ["$sentiments.positif_percent", "$sentiments.neutre_percent", "$sentiments.negatif_percent"]}, 0]},
                100
            ]
        },
        "sentiments.positif": {"$gt": 0}  # Pour éviter les cas où il n'y a pas de sentiments
    })

    validation_results["sentiments_percents_valid_region"] = sentiments_sum_region is None

    if not validation_results["sentiments_percents_valid_region"]:
        logger.error(f"Des pourcentages de sentiments régionaux ne totalisent pas 100%: {sentiments_sum_region['_id']}")

    logger.info(f"Validation des notes et sentiments: {validation_results}")
    return validation_results

def validate_roll_up_consistency(db):
    """Vérifie la cohérence entre les niveaux d'agrégation (villes → départements → régions)"""
    validation_results = {}

    # 1. Vérifier que le nombre total d'avis est cohérent à tous les niveaux
    pipeline_villes = [
        {"$group": {
            "_id": None,
            "total_avis": {"$sum": "$nombre_avis"},
            "total_villes": {"$sum": 1}
        }}
    ]

    pipeline_dept = [
        {"$group": {
            "_id": None,
            "total_avis": {"$sum": "$nombre_avis"},
            "total_villes": {"$sum": "$nombre_villes"}
        }}
    ]

    pipeline_region = [
        {"$group": {
            "_id": None,
            "total_avis": {"$sum": "$nombre_avis"},
            "total_villes": {"$sum": "$nombre_villes"}
        }}
    ]

    villes_stats = list(db.villes.aggregate(pipeline_villes))
    dept_stats = list(db.departements_stats.aggregate(pipeline_dept))
    region_stats = list(db.regions_stats.aggregate(pipeline_region))

    if villes_stats and dept_stats:
        villes_avis = villes_stats[0]["total_avis"]
        dept_avis = dept_stats[0]["total_avis"]
        villes_count = villes_stats[0]["total_villes"]
        dept_villes_count = dept_stats[0]["total_villes"]

        validation_results["avis_count_consistent_ville_dept"] = villes_avis == dept_avis
        validation_results["villes_count_consistent"] = villes_count == dept_villes_count

        logger.info(f"Cohérence avis villes-départements: {villes_avis} vs {dept_avis}, match={validation_results['avis_count_consistent_ville_dept']}")
        logger.info(f"Cohérence nombre de villes: {villes_count} vs {dept_villes_count}, match={validation_results['villes_count_consistent']}")

    if dept_stats and region_stats:
        dept_avis = dept_stats[0]["total_avis"]
        region_avis = region_stats[0]["total_avis"]
        dept_villes_count = dept_stats[0]["total_villes"]
        region_villes_count = region_stats[0]["total_villes"]

        validation_results["avis_count_consistent_dept_region"] = dept_avis == region_avis
        validation_results["villes_count_consistent_dept_region"] = dept_villes_count == region_villes_count

        logger.info(f"Cohérence avis départements-régions: {dept_avis} vs {region_avis}, match={validation_results['avis_count_consistent_dept_region']}")
        logger.info(f"Cohérence nombre de villes départements-régions: {dept_villes_count} vs {region_villes_count}, match={validation_results['villes_count_consistent_dept_region']}")

    return validation_results

def search_for_anomalies(db):
    """Recherche d'anomalies ou de valeurs inhabituelles dans les données agrégées"""
    anomalies = {}

    # 1. Rechercher des départements sans villes
    depts_sans_villes = list(db.departements_stats.find({"nombre_villes": 0}, {"_id": 1, "nom": 1}))
    anomalies["depts_sans_villes"] = [dept["nom"] for dept in depts_sans_villes]

    # 2. Rechercher des régions sans départements
    regions_sans_depts = list(db.regions_stats.find({"nombre_departements": 0}, {"_id": 1, "nom": 1}))
    anomalies["regions_sans_depts"] = [region["nom"] for region in regions_sans_depts]

    # 3. Rechercher des départements avec des notes extrêmes (très hautes ou très basses)
    depts_notes_extremes = list(db.departements_stats.find(
        {"$or": [
            {"notes.moyenne": {"$lt": 2}},
            {"notes.moyenne": {"$gt": 9}}
        ]},
        {"_id": 1, "nom": 1, "notes.moyenne": 1}
    ))
    anomalies["depts_notes_extremes"] = [
        {"nom": dept["nom"], "note": dept["notes"]["moyenne"]}
        for dept in depts_notes_extremes
    ]

    # 4. Rechercher des régions avec sentiments 100% positifs ou négatifs
    regions_sentiments_extremes = list(db.regions_stats.find(
        {"$or": [
            {"sentiments.positif_percent": 100},
            {"sentiments.negatif_percent": 100}
        ]},
        {"_id": 1, "nom": 1, "sentiments": 1}
    ))
    anomalies["regions_sentiments_extremes"] = [
        {
            "nom": region["nom"],
            "positif": region["sentiments"]["positif_percent"],
            "negatif": region["sentiments"]["negatif_percent"]
        }
        for region in regions_sentiments_extremes
    ]

    # 5. Vérifier les mots fréquents étrangement courts ou longs
    depts_mots_bizarres = []
    for dept in db.departements_stats.find({}, {"_id": 1, "nom": 1, "mots": 1}):
        for mot in dept.get("mots", []):
            if len(mot["mot"]) < 2 or len(mot["mot"]) > 30:
                depts_mots_bizarres.append({
                    "departement": dept["nom"],
                    "mot": mot["mot"],
                    "longueur": len(mot["mot"]),
                    "poids": mot["poids"]
                })
                break

    anomalies["mots_bizarres"] = depts_mots_bizarres[:10]  # Limiter à 10 exemples

    # Journaliser les anomalies trouvées
    for k, v in anomalies.items():
        if v:
            logger.warning(f"Anomalie trouvée - {k}: {v}")
        else:
            logger.info(f"Aucune anomalie de type '{k}' détectée")

    return anomalies

def generate_visualizations(db, output_dir):
    """Génère des visualisations pour aider à l'analyse des données agrégées"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Distribution des notes moyennes par département
    dept_notes = list(db.departements_stats.find({}, {"nom": 1, "notes.moyenne": 1}))
    if dept_notes:
        df_notes = pd.DataFrame([
            {"departement": d["nom"], "note_moyenne": d["notes"]["moyenne"]}
            for d in dept_notes
        ])

        plt.figure(figsize=(10, 6))
        sns.histplot(df_notes["note_moyenne"], bins=20, kde=True)
        plt.title("Distribution des notes moyennes par département")
        plt.xlabel("Note moyenne")
        plt.ylabel("Nombre de départements")
        plt.savefig(os.path.join(output_dir, "distribution_notes_departements.png"))
        plt.close()

        # Top 10 meilleurs départements
        top_depts = df_notes.sort_values("note_moyenne", ascending=False).head(10)
        plt.figure(figsize=(12, 6))
        sns.barplot(x="note_moyenne", y="departement", data=top_depts)
        plt.title("Top 10 des départements les mieux notés")
        plt.xlabel("Note moyenne")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "top10_departements.png"))
        plt.close()

    # 2. Carte de chaleur des sentiments par région
    region_sentiments = list(db.regions_stats.find({}, {"nom": 1, "sentiments": 1}))
    if region_sentiments:
        df_sentiments = pd.DataFrame([
            {
                "region": r["nom"],
                "positif": r["sentiments"].get("positif_percent", 0),
                "neutre": r["sentiments"].get("neutre_percent", 0),
                "negatif": r["sentiments"].get("negatif_percent", 0)
            }
            for r in region_sentiments
        ])

        # Trier par sentiment positif décroissant
        df_sentiments = df_sentiments.sort_values("positif", ascending=False)

        plt.figure(figsize=(12, 8))
        sentiment_columns = ["positif", "neutre", "negatif"]
        sns.heatmap(df_sentiments[sentiment_columns].T,
                    annot=True,
                    cmap="RdYlGn",
                    yticklabels=sentiment_columns,
                    xticklabels=df_sentiments["region"])
        plt.title("Répartition des sentiments par région (%)")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "sentiments_regions.png"))
        plt.close()

    # 3. Nuage de mots global (tous départements confondus)
    all_mots = []
    for dept in db.departements_stats.find({}, {"mots": 1}):
        for mot in dept.get("mots", []):
            all_mots.append({"mot": mot["mot"], "poids": mot["poids"]})

    if all_mots:
        mot_counter = Counter()
        for mot in all_mots:
            mot_counter[mot["mot"]] += mot["poids"]

        top_mots = pd.DataFrame([
            {"mot": mot, "frequence": freq}
            for mot, freq in mot_counter.most_common(30)
        ])

        plt.figure(figsize=(12, 6))
        sns.barplot(x="frequence", y="mot", data=top_mots)
        plt.title("Top 30 des mots les plus fréquents dans les avis")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "top_mots_frequents.png"))
        plt.close()

    # 4. Relation entre nombre d'avis et note moyenne
    dept_avis_notes = list(db.departements_stats.find({}, {"nom": 1, "nombre_avis": 1, "notes.moyenne": 1}))
    if dept_avis_notes:
        df_avis_notes = pd.DataFrame([
            {
                "departement": d["nom"],
                "nombre_avis": d["nombre_avis"],
                "note_moyenne": d["notes"]["moyenne"]
            }
            for d in dept_avis_notes
        ])

        plt.figure(figsize=(10, 6))
        sns.scatterplot(x="nombre_avis", y="note_moyenne", data=df_avis_notes)
        plt.title("Relation entre nombre d'avis et note moyenne par département")
        plt.xlabel("Nombre d'avis")
        plt.ylabel("Note moyenne")
        plt.savefig(os.path.join(output_dir, "relation_avis_notes.png"))
        plt.close()

    logger.info(f"Visualisations générées dans le répertoire {output_dir}")

def generate_summary_report(validation_results, output_dir):
    """Génère un rapport de synthèse en HTML"""
    html_report = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rapport de validation des données agrégées</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #1a5276; }}
            h2 {{ color: #2874a6; margin-top: 30px; }}
            .success {{ color: green; }}
            .warning {{ color: orange; }}
            .error {{ color: red; }}
            table {{ border-collapse: collapse; margin: 15px 0; }}
            table, th, td {{ border: 1px solid #ddd; }}
            th, td {{ padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .image-container {{ margin: 20px 0; }}
            .image-container img {{ max-width: 100%; }}
        </style>
    </head>
    <body>
        <h1>Rapport de validation des données agrégées</h1>
        <p>Date de génération: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        
        <h2>Résumé des validations</h2>
        <table>
            <tr>
                <th>Test</th>
                <th>Résultat</th>
            </tr>
    """

    # Ajouter les résultats des validations
    for category, results in validation_results.items():
        if isinstance(results, dict):
            for test, result in results.items():
                status_class = "success" if result else "error"
                html_report += f"""
                <tr>
                    <td>{category} - {test}</td>
                    <td class="{status_class}">{result}</td>
                </tr>
                """

    html_report += """
        </table>
        
        <h2>Visualisations</h2>
    """

    # Ajouter les visualisations
    for img_file in os.listdir(output_dir):
        if img_file.endswith('.png'):
            html_report += f"""
            <div class="image-container">
                <h3>{img_file.replace('.png', '').replace('_', ' ').title()}</h3>
                <img src="{img_file}" alt="{img_file}" />
            </div>
            """

    html_report += """
    </body>
    </html>
    """

    # Écrire le rapport HTML
    with open(os.path.join(output_dir, "rapport_validation.html"), "w") as f:
        f.write(html_report)

    logger.info(f"Rapport de validation généré: {os.path.join(output_dir, 'rapport_validation.html')}")

def export_stats_json(db, output_dir):
    """Exporte des statistiques clés au format JSON"""
    # 1. Collecter les statistiques générales
    general_stats = {
        "date_rapport": datetime.now().isoformat(),
        "nombre_villes": db.villes.count_documents({}),
        "nombre_avis": db.avis.count_documents({}),
        "nombre_departements": db.departements_stats.count_documents({}),
        "nombre_regions": db.regions_stats.count_documents({})
    }

    # 2. Top 10 des départements par note moyenne
    top_depts = list(db.departements_stats.find(
        {},
        {"_id": 1, "nom": 1, "nombre_villes": 1, "nombre_avis": 1, "notes.moyenne": 1}
    ).sort("notes.moyenne", -1).limit(10))

    top_depts_stats = [
        {
            "id": dept["_id"],
            "nom": dept["nom"],
            "nombre_villes": dept["nombre_villes"],
            "nombre_avis": dept["nombre_avis"],
            "note_moyenne": dept["notes"]["moyenne"]
        }
        for dept in top_depts
    ]

    # 3. Top 5 mots par fréquence
    all_mots = []
    for dept in db.departements_stats.find({}, {"mots": 1}):
        for mot in dept.get("mots", []):
            all_mots.append({"mot": mot["mot"], "poids": mot["poids"]})

    mot_counter = Counter()
    for mot in all_mots:
        mot_counter[mot["mot"]] += mot["poids"]

    top_mots = [
        {"mot": mot, "frequence": freq}
        for mot, freq in mot_counter.most_common(5)
    ]

    # 4. Statistiques des sentiments
    sentiments_pipeline = [
        {"$group": {
            "_id": None,
            "total_positif": {"$sum": "$sentiments.positif"},
            "total_neutre": {"$sum": "$sentiments.neutre"},
            "total_negatif": {"$sum": "$sentiments.negatif"}
        }}
    ]

    sentiments_stats = list(db.departements_stats.aggregate(sentiments_pipeline))

    if sentiments_stats:
        s = sentiments_stats[0]
        total = s["total_positif"] + s["total_neutre"] + s["total_negatif"]
        sentiments_global = {
            "positif": round((s["total_positif"] / total * 100), 1) if total > 0 else 0,
            "neutre": round((s["total_neutre"] / total * 100), 1) if total > 0 else 0,
            "negatif": round((s["total_negatif"] / total * 100), 1) if total > 0 else 0
        }
    else:
        sentiments_global = {"positif": 0, "neutre": 0, "negatif": 0}

    # Assembler les statistiques
    stats = {
        "general": general_stats,
        "top_departements": top_depts_stats,
        "top_mots": top_mots,
        "sentiments_global": sentiments_global
    }

    # Exporter au format JSON
    with open(os.path.join(output_dir, "stats_summary.json"), "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    logger.info(f"Statistiques exportées au format JSON: {os.path.join(output_dir, 'stats_summary.json')}")

def main():
    """Fonction principale de validation"""
    logger.info("Démarrage de la validation des données agrégées")

    try:
        # Créer le répertoire de sortie s'il n'existe pas
        output_dir = os.environ.get('OUTPUT_DIR', 'results')
        logger.info(f"Répertoire de sortie: {output_dir}")

        if not os.path.exists(output_dir):
            logger.info(f"Création du répertoire de sortie: {output_dir}")
            try:
                os.makedirs(output_dir)
                logger.info(f"Répertoire créé avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de la création du répertoire: {str(e)}")
                # Si le répertoire ne peut pas être créé, utiliser /tmp comme fallback
                output_dir = "/tmp"
                logger.info(f"Utilisation du répertoire temporaire: {output_dir}")

        # Test d'écriture dans le répertoire de sortie
        test_file = os.path.join(output_dir, "test_write.txt")
        try:
            with open(test_file, "w") as f:
                f.write("Test d'écriture")
            os.remove(test_file)
            logger.info(f"Test d'écriture dans {output_dir} réussi")
        except Exception as e:
            logger.error(f"Impossible d'écrire dans le répertoire {output_dir}: {str(e)}")
            # Si nous ne pouvons pas écrire, utiliser /tmp
            output_dir = "/tmp"
            logger.info(f"Utilisation du répertoire temporaire: {output_dir}")

        # Se connecter aux bases de données
        logger.info("Connexion aux bases de données...")
        mongo_client, mongo_db = connect_to_mongodb()

        # CORRECTION: Utiliser "is None" au lieu de "not mongo_db"
        if mongo_client is None or mongo_db is None:
            logger.error("Impossible de se connecter à MongoDB, arrêt de la validation")
            sys.exit(1)

        # Vérifier que MongoDB est accessible
        try:
            logger.info("Test de MongoDB - Liste des collections:")
            collections = mongo_db.list_collection_names()
            logger.info(f"Collections disponibles: {collections}")
        except Exception as e:
            logger.error(f"Erreur lors de l'accès à MongoDB: {str(e)}")
            if mongo_client is not None:
                mongo_client.close()
            sys.exit(1)

        # Se connecter à PostgreSQL
        pg_conn = connect_to_postgres()
        if pg_conn is None:
            logger.error("Impossible de se connecter à PostgreSQL, arrêt de la validation")
            if mongo_client is not None:
                mongo_client.close()
            sys.exit(1)

        # Vérifier que PostgreSQL est accessible
        try:
            logger.info("Test de PostgreSQL - Liste des tables:")
            with pg_conn.cursor() as cur:
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                tables = [row[0] for row in cur.fetchall()]
                logger.info(f"Tables disponibles: {tables}")
        except Exception as e:
            logger.error(f"Erreur lors de l'accès à PostgreSQL: {str(e)}")
            if mongo_client is not None:
                mongo_client.close()
            if pg_conn is not None:
                pg_conn.close()
            sys.exit(1)

        # Attendre que les collections nécessaires soient disponibles
        logger.info("Vérification des collections nécessaires...")
        required_collections = ["villes", "avis", "mots_villes", "departements_stats", "regions_stats"]

        # Vérifier quelles collections sont disponibles
        available_collections = mongo_db.list_collection_names()
        missing_collections = [coll for coll in required_collections if coll not in available_collections]

        if missing_collections:
            logger.warning(f"Collections manquantes: {missing_collections}")
            logger.warning("Tentative d'attente des collections manquantes...")

        if not wait_for_collections(mongo_db, required_collections):
            logger.error("Collections requises non disponibles, arrêt de la validation")
            if mongo_client is not None:
                mongo_client.close()
            if pg_conn is not None:
                pg_conn.close()
            sys.exit(1)

        # Exécuter les validations
        validation_results = {}
        logger.info("Début des validations...")

        # 1. Vérifier les statistiques de base des collections
        logger.info("Vérification des statistiques de base des collections...")
        try:
            stats, validation_results["collection_stats"] = check_collection_stats(mongo_db)
            logger.info("Statistiques de base vérifiées avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des statistiques: {str(e)}")
            validation_results["collection_stats"] = {"error": str(e)}

        # 2. Valider les agrégations par département
        logger.info("Validation des agrégations par département...")
        try:
            validation_results["department_validation"] = validate_department_aggregations(mongo_db, pg_conn)
            logger.info("Agrégations par département validées avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la validation des agrégations par département: {str(e)}")
            validation_results["department_validation"] = {"error": str(e)}

        # 3. Valider les agrégations par région
        logger.info("Validation des agrégations par région...")
        try:
            validation_results["region_validation"] = validate_region_aggregations(mongo_db, pg_conn)
            logger.info("Agrégations par région validées avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la validation des agrégations par région: {str(e)}")
            validation_results["region_validation"] = {"error": str(e)}

        # 4. Valider les calculs d'agrégation (notes, sentiments)
        logger.info("Validation des calculs d'agrégation...")
        try:
            validation_results["notes_validation"] = validate_notes_agregation(mongo_db)
            logger.info("Calculs d'agrégation validés avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la validation des calculs d'agrégation: {str(e)}")
            validation_results["notes_validation"] = {"error": str(e)}

        # 5. Vérifier la cohérence entre les niveaux d'agrégation
        logger.info("Vérification de la cohérence entre niveaux...")
        try:
            validation_results["rollup_consistency"] = validate_roll_up_consistency(mongo_db)
            logger.info("Cohérence entre niveaux vérifiée avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la cohérence entre niveaux: {str(e)}")
            validation_results["rollup_consistency"] = {"error": str(e)}

        # 6. Rechercher des anomalies
        logger.info("Recherche d'anomalies...")
        try:
            validation_results["anomalies"] = search_for_anomalies(mongo_db)
            logger.info("Recherche d'anomalies terminée avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la recherche d'anomalies: {str(e)}")
            validation_results["anomalies"] = {"error": str(e)}

        # Générer des visualisations
        logger.info("Génération des visualisations...")
        try:
            generate_visualizations(mongo_db, output_dir)
            logger.info("Visualisations générées avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la génération des visualisations: {str(e)}")

        # Exporter des statistiques au format JSON
        logger.info("Exportation des statistiques au format JSON...")
        try:
            export_stats_json(mongo_db, output_dir)
            logger.info("Statistiques exportées avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation des statistiques: {str(e)}")

        # Générer un rapport de synthèse
        logger.info("Génération du rapport de synthèse...")
        try:
            generate_summary_report(validation_results, output_dir)
            logger.info("Rapport de synthèse généré avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport de synthèse: {str(e)}")

        logger.info("Validation des données agrégées terminée avec succès")
        logger.info(f"Résultats disponibles dans le répertoire: {output_dir}")

    except Exception as e:
        logger.error(f"Erreur générale lors de la validation des données: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Fermer les connexions
        try:
            if 'mongo_client' in locals() and mongo_client is not None:
                mongo_client.close()
                logger.info("Connexion MongoDB fermée")
            if 'pg_conn' in locals() and pg_conn is not None:
                pg_conn.close()
                logger.info("Connexion PostgreSQL fermée")
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture des connexions: {str(e)}")

if __name__ == "__main__":
    main()