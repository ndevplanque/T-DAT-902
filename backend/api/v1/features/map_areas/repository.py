import v1.database.queries as q
import numpy as np
import json
import logs
import re
from v1.database.postgres import Postgres
from v1.models.bounds import Bounds
from v1.database.mongodb import MongoDB

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
    aggs_min_price = None
    aggs_max_price = None

    entity = extract_entity(query)
    ids=[]

    db = Postgres()
    for id, name, geo_json, nb_transactions, area_min_price, area_max_price, area_average_price in db.fetchall(query):
        # Filtrer les villes qui sont listées par arrondissements
        if entity == "cities":
            if name == "Paris":
                continue
            if name == "Marseille":
                continue

        # Filtrer les prix aberrants
        if area_average_price is not None and area_average_price < 500:
            area_average_price = None

        # Calculer les prix minimum et maximum pour la légende
        if area_average_price is not None and (aggs_min_price is None or area_average_price < aggs_min_price):
            aggs_min_price = area_average_price
        if area_average_price is not None and (aggs_max_price is None or area_average_price > aggs_max_price):
            aggs_max_price = area_average_price

        id_agglo = id

        # Liste des arrondissements de Paris
        arrondissements_paris = [
            75101, 75102, 75103, 75104, 75105, 75106, 75107, 75108, 75109, 75110,
            75111, 75112, 75113, 75114, 75115, 75116, 75117, 75118, 75119, 75120
        ]

        # Si l'ID correspond à un arrondissement parisien, le regrouper sous le code INSEE Paris
        if entity == 'cities' and int(id) in arrondissements_paris:
            id_agglo = 75056

        # Liste des arrondissements de Marseille
        arrondissements_marseille = [
            13201, 13202, 13203, 13204, 13205, 13206, 13207, 13208,
            13209, 13210, 13211, 13212, 13213, 13214, 13215, 13216
        ]

        # Si l'ID correspond à un arrondissement marseillais, le regrouper sous le code INSEE Paris
        if entity == 'cities' and int(id) in arrondissements_marseille:
            id_agglo = 13055

        ids.append(id)

        features.append({
            "type": "Feature",
            "properties": {
                "id": id,
                "id_agglo": id_agglo,
                "name": name,
                "price": area_average_price,
                "max_price": area_max_price,
                "min_price": area_min_price,
                "satisfaction": None,
                "word_cloud_url": f"api/v1/word-clouds/{entity}/{id_agglo}",
                "sentiments_url": f"api/v1/sentiments/{entity}/{id_agglo}",
            },
            "geometry": json.loads(geo_json)
        })

    db.close()

    if aggs_min_price is None:
        aggs_min_price = 0
    if aggs_max_price is None:
        aggs_max_price = 0

    with MongoDB() as mongo:
        cities = mongo.find(
            collection='villes',
            query={'city_id': {"$in": ids}},
            fields=MongoDB.only_fields(['city_id', 'notes', 'nombre_avis'])
        )

        for document in cities:
            if document and document['nombre_avis'] > 0:
                for feature in features:
                    if feature['properties']['id'] == document['city_id']:
                        feature['properties']['satisfaction'] = document['notes']['moyenne']

    return [features, aggs_min_price, aggs_max_price]
