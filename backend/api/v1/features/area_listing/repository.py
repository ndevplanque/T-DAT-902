from v1.database.postgres import Postgres
import v1.database.queries as q
import numpy as np
import re
import logs


def get_cities():
    data, aggs = parse_query_result(q.list_cities())
    return response_builder("Villes", data, aggs)


def get_departments():
    data, aggs = parse_query_result(q.list_departments())
    return response_builder("Départements", data, aggs)


def get_regions():
    data, aggs = parse_query_result(q.list_regions())
    return response_builder("Régions", data, aggs)


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
    data = []
    aggs_min_price = None
    aggs_max_price = None

    entity = extract_entity(query)

    db = Postgres()
    for id, name, nb_transactions, area_min_price, area_max_price, area_average_price in db.fetchall(query):
        # Filtrer les villes qui sont listées par arrondissements
        if entity == "cities":
            if name.startswith("Paris "):
                continue
            if name.startswith("Marseille "):
                continue

        # Filtrer les prix aberrants
        if area_average_price is not None and area_average_price < 500:
            area_average_price = None

        # Calculer les prix minimum et maximum pour la légende
        if area_average_price is not None and (aggs_min_price is None or area_average_price < aggs_min_price):
            aggs_min_price = area_average_price
        if area_average_price is not None and (aggs_max_price is None or area_average_price > aggs_max_price):
            aggs_max_price = area_average_price

        data.append({
            "id": id,
            "name": name,
            "price": area_average_price,
        })

    db.close()

    if aggs_min_price is None:
        aggs_min_price = 0
    if aggs_max_price is None:
        aggs_max_price = 0

    aggs = {
        "min_price": aggs_min_price,
        "max_price": aggs_max_price
    }

    return [data, aggs]


# Générer un prix aléatoire entre 1500 et 6000 €/m² pour chaque zone avec numpy
def generate_random_price():
    return round(np.random.uniform(1500, 6000), 2)


def response_builder(title, items, aggs):
    return {
        "title": title,
        "items": items,
        "aggs": aggs,
    }
