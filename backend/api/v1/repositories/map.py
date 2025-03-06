import psycopg2
import numpy as np

conn = None
cursor = None

def _connect():
    global conn, cursor
    conn = psycopg2.connect(dbname='gis_db', user='postgres', password='postgres', host='host.docker.internal', port='5432')
    cursor = conn.cursor()

def _close():
    global conn, cursor
    cursor.close()
    conn.close()

def get_cities():
    global cursor
    _connect()
    cursor.execute("SELECT city_id, name, ST_AsText(geom) FROM cities;")
    cities = []
    min_price = None
    max_price = None
    for city_id, name, geom_wkt in cursor.fetchall():
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
    _close()
    return layer_builder("Villes", cities, min_price, max_price)

def get_departments():
    global cursor
    _connect()
    cursor.execute("SELECT department_id, name, ST_AsText(geom) FROM departments;")
    departments = []
    min_price = None
    max_price = None
    for department_id, name, geom_wkt in cursor.fetchall():
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
    _close()
    return layer_builder("Départements", departments, min_price, max_price)

def get_regions():
    global cursor
    _connect()
    cursor.execute("SELECT region_id, name, ST_AsText(geom) FROM regions;")
    regions = []
    min_price = None
    max_price = None
    for region_id, name, geom_wkt in cursor.fetchall():
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
    _close()
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
