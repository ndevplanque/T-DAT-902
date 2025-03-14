from api.v1.database.postgres import Postgres
import api.v1.database.queries as q
import numpy as np

def get_cities_prices():
    db = Postgres()

    items = []
    min_price = None
    max_price = None

    for city_id, name in db.execute(q.list_cities_prices()):
        zone_price = generate_random_price() # En attendant d'avoir des données réelles
        # Mettre à jour min_price et max_price
        if min_price is None or zone_price < min_price:
            min_price = zone_price
        if max_price is None or zone_price > max_price:
            max_price = zone_price
        items.append({
            'name': name,
            'price': zone_price
        })

    aggs = {
        "min_price": min_price,
        "max_price": max_price,
    }

    db.close()
    return response_builder("Villes", items, aggs)

def get_departments_prices():
    db = Postgres()

    items = []
    min_price = None
    max_price = None

    for department_id, name in db.execute(q.list_departments_prices()):
        zone_price = generate_random_price() # En attendant d'avoir des données réelles
        # Mettre à jour min_price et max_price
        if min_price is None or zone_price < min_price:
            min_price = zone_price
        if max_price is None or zone_price > max_price:
            max_price = zone_price
        items.append({
            'name': name,
            'price': zone_price
        })

    aggs = {
        "min_price": min_price,
        "max_price": max_price,
    }

    db.close()
    return response_builder("Départements", items, aggs)

def get_regions_prices():
    db = Postgres()

    items = []
    min_price = None
    max_price = None

    for region_id, name in db.execute(q.list_regions_prices()):
        zone_price = generate_random_price() # En attendant d'avoir des données réelles
        # Mettre à jour min_price et max_price
        if min_price is None or zone_price < min_price:
            min_price = zone_price
        if max_price is None or zone_price > max_price:
            max_price = zone_price
        # Ajouter le nom et les coordonnées de la zone à la liste
        items.append({
            'name': name,
            'price': zone_price
        })

    aggs = {
        "min": min_price,
        "max": max_price,
    }

    db.close()
    return response_builder("Régions", items, aggs)

# Générer un prix aléatoire entre 1500 et 6000 €/m² pour chaque zone avec numpy
def generate_random_price():
    return round(np.random.uniform(1500, 6000), 2)

def response_builder(title, items, aggs):
    return {
        "title": title,
        "items": items,
        "aggs": aggs,
    }
