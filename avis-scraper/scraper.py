#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import pymongo
import time
import random
import logging
import re
import os
import concurrent.futures
from urllib.parse import urljoin
from tqdm import tqdm
import pandas as pd
from datetime import datetime

# Configuration du logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

# Configuration de la connexion MongoDB
def connect_to_mongodb():
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://root:rootpassword@mongodb:27017/')
    mongo_db = os.environ.get('MONGO_DB', 'villes_france')

    retry_count = 0
    max_retries = 5

    while retry_count < max_retries:
        try:
            client = pymongo.MongoClient(mongo_uri)
            # Ping pour vérifier la connexion
            client.admin.command('ping')
            logger.info("Connexion à MongoDB réussie")

            db = client[mongo_db]
            avis_collection = db["avis"]
            villes_collection = db["villes"]

            # Créer les index
            villes_collection.create_index([("city_id", 1)], unique=True)
            villes_collection.create_index([("code_insee", 1)])
            villes_collection.create_index([("department_id", 1)])

            avis_collection.create_index([("city_id", 1)])
            avis_collection.create_index([("avis_id", 1)])

            return client, avis_collection, villes_collection
        except pymongo.errors.ConnectionFailure as e:
            retry_count += 1
            wait_time = 5 * retry_count
            logger.warning(f"Échec de connexion à MongoDB (tentative {retry_count}/{max_retries}). Nouvelle tentative dans {wait_time}s. Erreur: {e}")
            time.sleep(wait_time)

    logger.error(f"Impossible de se connecter à MongoDB après {max_retries} tentatives")
    return None, None, None

# Headers pour simuler un navigateur web
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'https://www.bien-dans-ma-ville.fr/',
    'Connection': 'keep-alive',
}

# Créer une session requests pour réutiliser les connexions
session = requests.Session()
session.headers.update(headers)

# Fonction pour obtenir la page avec retry en cas d'échec - version optimisée
def get_page(url, max_retries=3, delay=1):
    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=5)  # Réduit timeout de 10s à 5s
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Statut HTTP {response.status_code} pour {url}")
        except requests.RequestException as e:
            logger.warning(f"Erreur lors de la requête {url} (tentative {attempt+1}/{max_retries}): {e}")

        # Attendre avant de réessayer (avec délai aléatoire pour éviter la détection)
        time.sleep(delay + random.uniform(0.5, 1))  # Réduit le délai aléatoire

    logger.error(f"Impossible de récupérer {url} après {max_retries} tentatives")
    return None

def get_all_ville_urls():
    """Récupère toutes les URLs des villes depuis le sitemap en ne gardant que celles au format ville-code/avis.html"""
    sitemap_url = "https://www.bien-dans-ma-ville.fr/sitemap-villeavis.xml"
    logger.info(f"Récupération des URLs des villes depuis le sitemap: {sitemap_url}")

    try:
        # Obtenir le contenu du sitemap
        sitemap_content = get_page(sitemap_url)
        if not sitemap_content:
            logger.error("Impossible de récupérer le sitemap")
            return []

        # Parser le XML
        soup = BeautifulSoup(sitemap_content, 'xml')  # Utiliser le parser 'xml' au lieu de 'html.parser'

        # Extraire toutes les URLs
        url_tags = soup.select("url loc")

        if not url_tags:
            # Essayer un autre sélecteur si le premier ne fonctionne pas
            url_tags = soup.select("loc")

        if not url_tags:
            logger.error("Aucune URL trouvée dans le sitemap. Format inattendu.")
            # Essayer de parser manuellement avec des expressions régulières
            urls = re.findall(r'<loc>(https://www\.bien-dans-ma-ville\.fr/[^<]+/avis\.html)</loc>', sitemap_content)
            if urls:
                # Filtrer les URLs pour ne garder que celles au format ville-code/avis.html
                pattern = re.compile(r'https://www\.bien-dans-ma-ville\.fr/[^/]+-\d+/avis\.html$')
                valid_urls = [url for url in urls if pattern.match(url)]

                total_urls = len(urls)
                valid_count = len(valid_urls)
                excluded_count = total_urls - valid_count

                logger.info(f"URLs récupérées via regex: {total_urls} total")
                logger.info(f"URLs valides (format ville-code/avis.html): {valid_count}")
                logger.info(f"URLs ignorées: {excluded_count}")

                return valid_urls
            return []

        # Extraire les URLs depuis les balises <loc>
        all_urls = [tag.text.strip() for tag in url_tags]

        # Filtrer pour conserver uniquement le format ville-code/avis.html
        pattern = re.compile(r'https://www\.bien-dans-ma-ville\.fr/[^/]+-\d+/avis\.html$')
        valid_urls = [url for url in all_urls if pattern.match(url)]

        # Comptages pour les statistiques
        total_urls = len(all_urls)
        valid_count = len(valid_urls)
        quartier_count = len([url for url in all_urls if "/quartier-" in url])
        other_invalid = total_urls - valid_count - quartier_count

        logger.info(f"Total des URLs trouvées dans le sitemap: {total_urls}")
        logger.info(f"URLs valides (format ville-code/avis.html): {valid_count}")
        logger.info(f"URLs de quartiers ignorées: {quartier_count}")
        logger.info(f"Autres URLs invalides ignorées: {other_invalid}")

        return valid_urls

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des URLs du sitemap: {e}")
        return []

# Extraire les informations sur une ville
def get_ville_info(url):
    html = get_page(url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')

    # Obtenir le nom et le code postal de la ville
    title = soup.select_one("h1")
    if not title:
        logger.warning(f"Impossible de trouver le titre pour {url}")
        return None

    title_text = title.text.strip()

    # Extraire nom et code postal
    nom_ville = re.sub(r'\s*<small>.*?</small>\s*', '', title_text) if '<small>' in title_text else title_text
    code_postal_match = re.search(r'<small>(\d+)</small>', str(title)) if title else None
    code_postal = code_postal_match.group(1) if code_postal_match else ""

    # Extraire le code INSEE à partir de l'URL
    code_insee = ""
    insee_match = re.search(r'/([^/]+)-(\d+)/avis\.html', url)
    if insee_match:
        code_insee = insee_match.group(2)

    # Extraire department_id (2 premiers chiffres du code INSEE)
    department_id = code_insee[:2] if code_insee and len(code_insee) >= 2 else ""

    # Pour les DOM-TOM qui ont un format différent (97X)
    if department_id == "97" and len(code_insee) >= 3:
        department_id = code_insee[:3]

    # Récupérer les notes moyennes
    notes = {
        "moyenne": 0,
        "securite": 0,
        "education": 0,
        "sport_loisir": 0,
        "environnement": 0,
        "vie_pratique": 0
    }

    # Note moyenne globale
    note_moyenne = soup.select_one("div.total")
    if note_moyenne:
        try:
            notes["moyenne"] = float(note_moyenne.text.strip().split('/')[0])
        except (ValueError, IndexError):
            pass

    # Notes par catégorie
    note_rows = soup.select("table.bloc_chiffre tr")
    for row in note_rows:
        category = row.select_one("td")
        note = row.select_one("td span")
        if category and note:
            category_text = category.text.strip().lower()
            try:
                note_value = float(note.text.strip())

                if "sécurité" in category_text:
                    notes["securite"] = note_value
                elif "éducation" in category_text:
                    notes["education"] = note_value
                elif "sport" in category_text:
                    notes["sport_loisir"] = note_value
                elif "environnement" in category_text:
                    notes["environnement"] = note_value
                elif "vie pratique" in category_text:
                    notes["vie_pratique"] = note_value
            except ValueError:
                pass

    # Obtenir le nombre total d'avis
    nb_avis = 0
    nb_avis_element = soup.select_one("div.nbtotal")
    if nb_avis_element:
        nb_avis_match = re.search(r'sur (\d+) commentaires', nb_avis_element.text)
        if nb_avis_match:
            nb_avis = int(nb_avis_match.group(1))

    # Créer l'objet ville
    ville_info = {
        "nom": nom_ville,
        "code_postal": code_postal,
        "code_insee": code_insee,  # Ajout du code INSEE
        "city_id": code_insee,     # Utiliser code_insee comme city_id pour mapper avec PostgreSQL
        "department_id": department_id,  # Ajout du department_id
        "url": url,
        "notes": notes,
        "nombre_avis": nb_avis,
        "date_scraping": datetime.now(),
        "statut_traitement": "non_traite"  # Pour indiquer que les mots n'ont pas encore été extraits
    }

    return ville_info

# Version corrigée pour extraire les avis d'une ville (avec gestion de la pagination et bulk write correct)
def scrape_avis_ville(url, avis_collection, ville_id, city_id):
    from pymongo.operations import UpdateOne

    page_num = 1
    has_next_page = True
    total_avis = 0

    # Construire l'URL de base sans paramètres de page
    base_url = url.split('?')[0]

    while has_next_page:
        current_url = base_url if page_num == 1 else f"{base_url}?page={page_num}#commentaires"
        logger.info(f"Scraping des avis: {current_url}")

        html = get_page(current_url)
        if not html:
            break

        soup = BeautifulSoup(html, 'html.parser')

        # Extraire tous les avis de la page
        avis_elements = soup.select("div.commentaire:not(.reponse):not(.bdmv)")
        if not avis_elements:
            logger.warning(f"Aucun avis trouvé sur {current_url}")
            break

        # Liste pour collecter tous les avis avant de les insérer en masse
        avis_batch = []

        for avis_elem in avis_elements:
            try:
                # Extraire les informations de l'avis
                auteur = avis_elem.select_one("div.auteur")
                auteur_text = auteur.text.strip() if auteur else "Anonyme"

                # Récupérer la note globale
                note_elem = avis_elem.select_one("span.note_total")
                note_globale = float(note_elem.text.strip()) if note_elem else 0

                # Récupérer les notes spécifiques
                notes_spec = avis_elem.select("div.notes span")
                notes = {
                    "securite": float(notes_spec[0].text) if len(notes_spec) > 0 else 0,
                    "education": float(notes_spec[1].text) if len(notes_spec) > 1 else 0,
                    "sport_loisir": float(notes_spec[2].text) if len(notes_spec) > 2 else 0,
                    "environnement": float(notes_spec[3].text) if len(notes_spec) > 3 else 0,
                    "vie_pratique": float(notes_spec[4].text) if len(notes_spec) > 4 else 0
                }

                # Date de l'avis
                date_elem = avis_elem.select_one("div.date")
                date = date_elem.text.strip() if date_elem else ""

                # Texte de l'avis
                description_elem = avis_elem.select_one("p.description")
                description = description_elem.text.strip() if description_elem else ""

                # Votes (pouces haut / bas)
                pouces_haut = avis_elem.select_one("div.pouce[data-pouce='1'] span")
                pouces_bas = avis_elem.select_one("div.pouce[data-pouce='0'] span")
                nb_pouces_haut = int(pouces_haut.text) if pouces_haut else 0
                nb_pouces_bas = int(pouces_bas.text) if pouces_bas else 0

                avis_id = avis_elem.get('data-pouce', '')

                # Créer l'objet avis
                avis = {
                    "ville_id": ville_id,
                    "city_id": city_id,
                    "avis_id": avis_id,
                    "auteur": auteur_text,
                    "date": date,
                    "note_globale": note_globale,
                    "notes": notes,
                    "description": description,
                    "pouces_haut": nb_pouces_haut,
                    "pouces_bas": nb_pouces_bas,
                    "date_scraping": datetime.now(),
                    "statut_traitement": "non_traite"
                }

                # Ajouter à notre batch en utilisant l'objet UpdateOne de pymongo
                avis_batch.append(
                    UpdateOne(
                        {"ville_id": ville_id, "avis_id": avis_id},
                        {"$set": avis},
                        upsert=True
                    )
                )

                total_avis += 1

            except Exception as e:
                logger.error(f"Erreur lors de l'extraction d'un avis: {e}")

        # Insérer les avis en masse si le batch n'est pas vide
        if avis_batch:
            try:
                # Utiliser bulk write pour insérer en masse
                avis_collection.bulk_write(avis_batch, ordered=False)
            except pymongo.errors.BulkWriteError as bwe:
                # Ignorer les erreurs de duplication
                logger.warning(f"Certains avis n'ont pas pu être insérés: {bwe.details}")

        # Vérifier s'il y a une page suivante
        pagination = soup.select_one("div.pagination")
        next_page_link = pagination.select_one("a.next") if pagination else None
        has_next_page = bool(next_page_link)
        page_num += 1

        # Attendre entre les requêtes (délai réduit)
        if has_next_page:
            time.sleep(random.uniform(0.5, 1))

    logger.info(f"Total des avis extraits pour {url}: {total_avis}")
    return total_avis

# Fonction pour traiter une ville complète (infos + avis)
def process_ville(url, client=None, villes_collection=None, avis_collection=None):
    """Traite une ville complète (infos + avis)"""
    try:
        # Si les collections ne sont pas fournies, créer des connexions locales
        if client is None or villes_collection is None or avis_collection is None:
            client_local, avis_collection_local, villes_collection_local = connect_to_mongodb()
            if client_local is None:
                return 0
            client = client_local
            villes_collection = villes_collection_local
            avis_collection = avis_collection_local
            local_connection = True
        else:
            local_connection = False

        logger.info(f"Traitement de la ville: {url}")

        # Obtenir les informations sur la ville
        ville_info = get_ville_info(url)
        if not ville_info:
            logger.warning(f"Impossible d'obtenir les infos pour: {url}")
            return 0

        city_id = ville_info.get("city_id", "")

        logger.info(f"Ville: {ville_info['nom']} (CP: {ville_info['code_postal']}, INSEE: {city_id}), Nb avis: {ville_info['nombre_avis']}")

        # Insérer ou mettre à jour les informations de la ville
        try:
            ville_result = villes_collection.update_one(
                {"url": url},
                {"$set": ville_info},
                upsert=True
            )

            # Récupérer l'ID de la ville
            if ville_result.upserted_id:
                ville_id = ville_result.upserted_id
            else:
                ville_doc = villes_collection.find_one({"url": url})
                ville_id = ville_doc["_id"]

            # Scraper tous les avis de la ville
            nb_avis = scrape_avis_ville(url, avis_collection, ville_id, city_id)

            # Fermer la connexion locale si nécessaire
            if local_connection:
                client.close()

            return nb_avis

        except pymongo.errors.DuplicateKeyError:
            logger.warning(f"Conflit de clé pour {url}, city_id={city_id}")
            ville_doc = villes_collection.find_one({"city_id": city_id})
            if ville_doc:
                ville_id = ville_doc["_id"]
                nb_avis = scrape_avis_ville(url, avis_collection, ville_id, city_id)

                # Fermer la connexion locale si nécessaire
                if local_connection:
                    client.close()

                return nb_avis

        # Fermer la connexion locale si nécessaire
        if local_connection:
            client.close()

        return 0

    except Exception as e:
        logger.error(f"Erreur lors du traitement de {url}: {e}")
        return 0

# Fonction principale avec multithreading
def main():
    """Version optimisée de la fonction principale utilisant le sitemap"""
    logger.info("Démarrage du scraping des avis de villes")

    # Se connecter à MongoDB
    client, avis_collection, villes_collection = connect_to_mongodb()
    if not client:
        return

    try:
        # Options de configuration
        test_mode = os.environ.get('TEST_MODE', 'false').lower() == 'true'
        max_villes = int(os.environ.get('MAX_VILLES', '0'))  # 0 = toutes les villes
        max_workers = int(os.environ.get('MAX_WORKERS', '8'))  # Nombre de threads parallèles
        batch_size = int(os.environ.get('BATCH_SIZE', '50'))  # Traiter les villes par lots

        # URLs de test
        test_urls = [
            "https://www.bien-dans-ma-ville.fr/strasbourg-67482/avis.html",
            "https://www.bien-dans-ma-ville.fr/paris-75056/avis.html",
            "https://www.bien-dans-ma-ville.fr/lyon-69123/avis.html"
        ]

        # Mode test ou mode normal
        if test_mode:
            logger.info("Mode test activé avec URLs spécifiques")
            ville_urls = test_urls
        else:
            # Vérifier si on est en mode mise à jour
            update_mode = os.environ.get('UPDATE_MODE', 'false').lower() == 'true'
            if update_mode:
                # En mode mise à jour, obtenir d'abord les statistiques actuelles
                existing_count = villes_collection.count_documents({})
                existing_avis_count = avis_collection.count_documents({})
                existing_urls = set(v["url"] for v in villes_collection.find({}, {"url": 1}))
                logger.info(f"État actuel de la base: {existing_count} villes, {existing_avis_count} avis")

                # Obtenir toutes les URLs du sitemap (avec le nouveau filtre)
                all_sitemap_urls = get_all_ville_urls()

                # Vérifier celles qui sont déjà dans la base
                already_in_db = [url for url in all_sitemap_urls if url in existing_urls]

                # Filtrer pour ne garder que les nouvelles URLs
                ville_urls = [url for url in all_sitemap_urls if url not in existing_urls]

                logger.info(f"Mode mise à jour: {len(already_in_db)} villes déjà dans la base")
                logger.info(f"Mode mise à jour: {len(ville_urls)} nouvelles villes à traiter")
            else:
                # Mode normal: obtenir toutes les URLs des villes depuis le sitemap
                ville_urls = get_all_ville_urls()
                logger.info(f"Mode normal: {len(ville_urls)} villes à traiter")


        # Limiter le nombre de villes si spécifié
        if max_villes > 0 and len(ville_urls) > max_villes:
            logger.info(f"Limitation à {max_villes} villes (sur {len(ville_urls)} disponibles)")
            ville_urls = ville_urls[:max_villes]

        total_villes = len(ville_urls)
        if total_villes == 0:
            logger.info("Aucune ville à traiter, fin du script")
            return

        logger.info(f"Début du scraping pour {total_villes} villes avec {max_workers} threads")

        # Traiter les villes par lots pour une meilleure gestion de la mémoire
        total_avis = 0
        with tqdm(total=total_villes, desc="Scraping des villes") as pbar:
            for i in range(0, total_villes, batch_size):
                batch = ville_urls[i:i+batch_size]
                logger.info(f"Traitement du lot {i//batch_size + 1}/{(total_villes-1)//batch_size + 1} ({len(batch)} villes)")

                # Utiliser ThreadPoolExecutor pour paralléliser le lot
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Créer un futur pour chaque ville, en passant les collections MongoDB
                    future_to_url = {
                        executor.submit(process_ville, url, client, villes_collection, avis_collection): url
                        for url in batch
                    }

                    # Traiter les résultats au fur et à mesure
                    for future in concurrent.futures.as_completed(future_to_url):
                        url = future_to_url[future]
                        try:
                            nb_avis = future.result()
                            total_avis += nb_avis
                            logger.debug(f"Ville traitée: {url} - {nb_avis} avis")
                            pbar.update(1)
                        except Exception as e:
                            logger.error(f"Erreur lors du traitement de {url}: {e}")
                            pbar.update(1)

        logger.info(f"Scraping terminé! Total des villes: {total_villes}, Total des avis: {total_avis}")

    except Exception as e:
        logger.error(f"Erreur générale: {e}")
    finally:
        # Ne pas oublier de fermer la connexion
        if client:
            client.close()

if __name__ == "__main__":
    main()