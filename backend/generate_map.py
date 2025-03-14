import os
from dotenv import load_dotenv
import logging
import folium
from shapely import wkt
from shapely.geometry import shape, Polygon
import api.v1.repositories.map as repository
from flask import send_file

# A exécuter depuis le container Docker "backend", en allant dans Exec, puis écrire "python3 generate_map.py"

load_dotenv()
V1_MAP_FILEPATH = os.getenv('V1_MAP_FILEPATH')
COLORS = ["#060", "#282", "#3C3", "#7F0", "#AF2", "#FF0", "#FD0", "#FA0", "#F80", "#F64", "#F40", "#F00"]
logging.basicConfig(level=logging.INFO)

def build_map():
    """Construit la carte en utilisant les données de la base de données."""

    logging.info("Récupération des données de la carte...")
    data = get_map_data()
    logging.info(f"Données récupérées.")

    map_instance = create_map()

    logging.info("Ajout des données à la carte...")
    map_instance = populate_map(map_instance, data)
    logging.info("Données ajoutées.")

    logging.info("Sauvegarde de la carte...")
    map_instance.save(V1_MAP_FILEPATH)
    if os.path.exists(V1_MAP_FILEPATH) and os.path.getsize(V1_MAP_FILEPATH) > 0:
        logging.info(f"Carte générée et sauvegardée dans {V1_MAP_FILEPATH}.")
    else:
        logging.error("Le fichier de la carte est vide ou n'a pas été généré correctement.")

def get_map_data():
    """Récupère les données des différentes couches de la carte."""
    cities = repository.get_cities()
    if "zones" in cities and isinstance(cities["zones"], list) and not cities["zones"]:
        raise ValueError("Erreur : La liste 'cities' est vide.")

    departments = repository.get_departments()
    if "zones" in departments and isinstance(departments["zones"], list) and not departments["zones"]:
        raise ValueError("Erreur : La liste 'departments' est vide.")

    regions = repository.get_regions()
    if "zones" in regions and isinstance(regions["zones"], list) and not regions["zones"]:
        raise ValueError("Erreur : La liste 'regions' est vide.")

    return {
        "layers": {
            "cities": cities,
            "departments": departments,
            "regions": regions,
        }
    }

def create_map():
    """Génère la carte Folium et l'enregistre dans un fichier HTML."""
    token = os.getenv('MAPBOX_ACCESS_TOKEN')

    map_instance = folium.Map(
        location=[48.584614, 7.750713],  # Strasbourg
        zoom_start=10,
        tiles=None
    )

    folium.TileLayer(
        tiles=f"https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/{{z}}/{{x}}/{{y}}?access_token={token}",
        attr="Mapbox",
        name="Carte Mapbox",
        overlay=False,
        control=False
    ).add_to(map_instance)

    return map_instance

def populate_map(map_instance, data):
    """Ajoute les couches de données à la carte."""
    for key, layer in data["layers"].items():
        if "zones" not in layer:
            continue  # Si la couche ne contient pas de zones, on passe à la suivante

        map_layer = folium.FeatureGroup(
            name=layer["name"],
            show=layer["shown_by_default"]
        )
        for zone in layer["zones"]:
            if "geom_wkt" not in zone or "price" not in zone:  # Vérification de la présence des données essentielles
                continue

            zone_geometry = shape(wkt.loads(zone["geom_wkt"]))
            simplified_geometry = simplify_geometry(zone_geometry, tolerance=0.01)  # Simplification avec tolérance
            geojson(simplified_geometry, zone, layer["min_price"], layer["max_price"]).add_to(map_layer)
        map_instance.add_child(map_layer)

    folium.LayerControl().add_to(map_instance)

    return map_instance

def get_fill_color(zone_price, min_price, max_price):
    """Calcule la couleur de remplissage d'une zone en fonction de son prix."""
    if min_price == max_price:  # Évite la division par zéro
        return COLORS[-1]
    normalized_price = (zone_price - min_price) / (max_price - min_price)
    return COLORS[int(normalized_price * (len(COLORS) - 1))]

def geojson(coords, zone, min_price, max_price):
    """Retourne un objet GeoJson configuré pour une zone donnée."""
    return folium.GeoJson(
        data=coords.__geo_interface__,
        style_function=lambda feature: {
            'fillColor': get_fill_color(zone["price"], min_price, max_price),
            'color': 'white',
            'weight': 1,
            'fillOpacity': 0.5
        },
        tooltip=zone["name"]
    )

def simplify_geometry(geometry, tolerance=0.01):
    """Simplifie une géométrie (polygone) en fonction de la tolérance spécifiée."""
    if isinstance(geometry, Polygon):  # Vérifie si la géométrie est un polygone
        return geometry.simplify(tolerance, preserve_topology=True)
    else:
        # Si la géométrie n'est pas un polygone, la renvoyer telle quelle.
        # (On peut éventuellement ajouter un traitement pour d'autres types de géométries)
        return geometry

build_map()  # Génère la carte