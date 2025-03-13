from api.v1.database.postgres import Postgres
import api.v1.database.queries as q
import numpy as np

def get_cities():
    db = Postgres()

    cities = []
    min_price = None
    max_price = None

    for city_id, name, geom_wkt in db.execute(q.list_cities()):
        zone_price = generate_random_price() # En attendant d'avoir des données réelles
        # Mettre à jour min_price et max_price
        if min_price is None or zone_price < min_price:
            min_price = zone_price
        if max_price is None or zone_price > max_price:
            max_price = zone_price
        cities.append({
            'name': name,
            'geom_wkt': geom_wkt,
            'price': zone_price
        })

    db.close()
    return layer_builder("Villes", cities, min_price, max_price)

def get_departments():
    db = Postgres()

    departments = []
    min_price = None
    max_price = None

    for department_id, name, geom_wkt in db.execute(q.list_departments()):
        zone_price = generate_random_price() # En attendant d'avoir des données réelles
        # Mettre à jour min_price et max_price
        if min_price is None or zone_price < min_price:
            min_price = zone_price
        if max_price is None or zone_price > max_price:
            max_price = zone_price
        departments.append({
            'name': name,
            'geom_wkt': geom_wkt,
            'price': zone_price
        })

    db.close()
    return layer_builder("Départements", departments, min_price, max_price)

def get_regions():
    db = Postgres()

    regions = []
    min_price = None
    max_price = None

    for region_id, name, geom_wkt in db.execute(q.list_regions()):
        zone_price = generate_random_price() # En attendant d'avoir des données réelles
        # Mettre à jour min_price et max_price
        if min_price is None or zone_price < min_price:
            min_price = zone_price
        if max_price is None or zone_price > max_price:
            max_price = zone_price
        # Ajouter le nom et les coordonnées de la zone à la liste
        regions.append({
            'name': name,
            'geom_wkt': geom_wkt,
            'price': zone_price
        })

    db.close()
    return layer_builder("Régions", regions, min_price, max_price)

# Générer un prix aléatoire entre 1500 et 6000 €/m² pour chaque zone avec numpy
def generate_random_price():
    return round(np.random.uniform(1500, 6000), 2)

def layer_builder(name, zones, min_price, max_price):
    return {
        "name": name,
        "zones": zones,
        "min_price": min_price,
        "max_price": max_price,
        "shown_by_default": is_shown(name)
    }

def is_shown(name):
    return name == "Départements"
