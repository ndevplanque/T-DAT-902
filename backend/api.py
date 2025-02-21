from flask import Flask, jsonify
import pandas as pd
import numpy as np
import json

app = Flask(__name__)

@app.route('/', methods=['GET'])
def root():
    return api_v1_health()

@app.route('/api/v1/health', methods=['GET'])
def api_v1_health():
    return jsonify({"success": True})

@app.route('/api/v1/data', methods=['GET'])
def api_v1_data():
    return jsonify({"message": "Hello from Flask!", "value": 42})

# Charger le fichier geojson à partir du même dossier
def load_geojson():
    with open('epci-1000m.geojson', 'r') as file:
        data = json.load(file)
    return data

# Générer un prix aléatoire entre 1500 et 6000 €/m² pour chaque zone avec numpy
def generate_random_price():
    return round(np.random.uniform(1500, 6000), 2)

@app.route('/api/v1/map', methods=['GET'])
def api_v1_map():
    # Charger les données du fichier geojson
    geojson_data = load_geojson()

    zones = []
    min_price = None
    max_price = None

    for feature in geojson_data['features']:
        zone_name = feature['properties']['nom']
        zone_coordinates = feature['geometry']['coordinates'][0]

        # Générer un prix aléatoire pour la zone (ou utiliser tes données réelles)
        zone_price = generate_random_price()

        # Mettre à jour min_price et max_price
        if min_price is None or zone_price < min_price:
            min_price = zone_price
        if max_price is None or zone_price > max_price:
            max_price = zone_price

        # Correction de l'inversion des coordonnées (GeoJSON a souvent [longitude, latitude])
        # Ici, on inverse pour avoir [latitude, longitude]
        corrected_coordinates = [[coord[1], coord[0]] for coord in zone_coordinates]

        zones.append({
            'name': zone_name,
            'coordinates': corrected_coordinates,
            'price': zone_price
        })

    return jsonify({
        'zones': zones,
        'min_price': min_price,
        'max_price': max_price,
    })