from flask import jsonify
import json
import pandas as pd
import numpy as np

# Charger le fichier geojson à partir du même dossier
def load_geojson():
    with open('api/v1/resources/epci-1000m.geojson', 'r') as file:
        data = json.load(file)
    return data

# Générer un prix aléatoire entre 1500 et 6000 €/m² pour chaque zone avec numpy
def generate_random_price():
    return round(np.random.uniform(1500, 6000), 2)

def layer_builder(name, zones, min_price, max_price):
    return {
        "name": name,
        "zones": zones,
        "min_price": min_price,
        "max_price": max_price,
    }

def layer_from_geojson(layer_name, geojson_data):
    zones = []
    min_price = None
    max_price = None

    for feature in geojson_data['features']:
        zone_name = feature['properties']['nom']
        zone_coordinates = feature['geometry']['coordinates'][0]
        zone_price = generate_random_price()

        # Mettre à jour min_price et max_price
        if min_price is None or zone_price < min_price:
            min_price = zone_price
        if max_price is None or zone_price > max_price:
            max_price = zone_price

        # Correction de l'inversion des coordonnées (GeoJSON a souvent [longitude, latitude])
        corrected_coordinates = [[coord[1], coord[0]] for coord in zone_coordinates]

        zones.append({
            'name': zone_name,
            'coordinates': corrected_coordinates,
            'price': zone_price
        })

    return layer_builder(layer_name, zones, min_price, max_price)

def map():
    geojson_data = load_geojson()

    communes = layer_from_geojson('Communes', geojson_data)
    departements = layer_from_geojson('Départements', geojson_data)
    regions = layer_from_geojson('Régions', geojson_data)

    return {"layers": [communes, departements, regions]}
