import v1.database.queries as q
import numpy as np
import json
import re
from v1.database.postgres import Postgres
from v1.models.bounds import Bounds


def get_feature_collection(entity, bounds: Bounds):
    if entity == "cities":
        fc = get_cities_feature_collection(bounds)
        if len(fc['features']) < 500:
            return fc
        else:
            # Si plus de 500 villes, renvoyer des départements à la place
            return get_feature_collection("departments", bounds)

    elif entity == "departments":
        fc = get_departments_feature_collection(bounds)
        if len(fc['features']) < 500:
            return fc
        else:
            # Si plus de 500 départements, renvoyer des régions à la place
            return get_feature_collection("regions", bounds)

    elif entity == "regions":
        return get_regions_feature_collection(bounds)

    else:
        raise ValueError("Invalid entity")


def get_cities_feature_collection(bounds: Bounds):
    features, min_price, max_price = parse_query_result(q.list_cities_map_areas(bounds))
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "name": "Villes",
            "min_price": min_price,
            "max_price": max_price,
            "show": True
        }
    }


def get_departments_feature_collection(bounds: Bounds):
    features, min_price, max_price = parse_query_result(q.list_departments_map_areas(bounds))
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "name": "Départements",
            "min_price": min_price,
            "max_price": max_price,
            "show": True
        }
    }


def get_regions_feature_collection(bounds: Bounds):
    features, min_price, max_price = parse_query_result(q.list_regions_map_areas(bounds))
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "name": "Régions",
            "min_price": min_price,
            "max_price": max_price,
            "show": True
        }
    }


def extract_entity(query):
    try:
        match = re.search(r'FROM\s+(\w+)', query)
        entity = match.group(1)
        if entity in ["cities", "departments", "regions"]:
            return entity
        return None
    except AttributeError:
        return None


def parse_query_result(query):
    features = []
    min_price = None
    max_price = None

    entity = extract_entity(query)

    db = Postgres()
    for id, name, geo_json in db.fetchall(query):
        zone_price = generate_random_price()
        if min_price is None or zone_price < min_price:
            min_price = zone_price
        if max_price is None or zone_price > max_price:
            max_price = zone_price
        features.append({
            "type": "Feature",
            "properties": {
                "id": id,
                "name": name,
                "price": zone_price,
                "word_cloud_url": f"api/v1/word-clouds/{entity}/{id}",
                "sentiments_url": f"api/v1/sentiments/{entity}/{id}",
            },
            "geometry": json.loads(geo_json)
        })

    db.close()

    if min_price is None:
        min_price = 0
    if max_price is None:
        max_price = 0

    return [features, min_price, max_price]


# Générer un prix aléatoire entre 1500 et 6000 €/m² pour chaque zone avec numpy
def generate_random_price():
    return round(np.random.uniform(1500, 6000), 2)
