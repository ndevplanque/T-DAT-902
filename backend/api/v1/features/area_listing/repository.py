from v1.database.postgres import Postgres
import v1.database.queries as q
import numpy as np


def get_cities():
    data, aggs = parse_query_result(q.list_cities())
    return response_builder("Villes", data, aggs)


def get_departments():
    data, aggs = parse_query_result(q.list_departments())
    return response_builder("Départements", data, aggs)


def get_regions():
    data, aggs = parse_query_result(q.list_regions())
    return response_builder("Régions", data, aggs)


def parse_query_result(query):
    data = []
    min_price = None
    max_price = None

    db = Postgres()
    for id, name in db.fetchall(query):
        zone_price = generate_random_price()
        if min_price is None or zone_price < min_price:
            min_price = zone_price
        if max_price is None or zone_price > max_price:
            max_price = zone_price
        data.append({
            "id": id,
            "name": name,
            "price": zone_price,
        })

    db.close()

    if min_price is None:
        min_price = 0
    if max_price is None:
        max_price = 0

    aggs = {
        "min_price": min_price,
        "max_price": max_price
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
