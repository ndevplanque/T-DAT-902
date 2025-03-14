import os
from dotenv import load_dotenv
import logging
import folium
from shapely import wkt
import api.v1.repositories.map as repository
from flask import send_file

load_dotenv()
V1_MAP_FILEPATH = os.getenv('V1_MAP_FILEPATH')
COLORS = ["#060", "#282", "#3C3", "#7F0", "#AF2", "#FF0", "#FD0", "#FA0", "#F80", "#F64", "#F40", "#F00"]
logging.basicConfig(level=logging.INFO)

def send_html():
    """Renvoie le contenu HTML de la carte."""
    init() # Initialise la carte si elle n'existe pas
    return send_file(V1_MAP_FILEPATH)

def init():
    """Initialise la carte en la générant si elle n'existe pas."""
    if not os.path.exists(V1_MAP_FILEPATH):  # Vérifie si le fichier n'existe pas
        build_map()  # Génère la carte

def build_map():
    """Construit la carte en utilisant les données de la base de données."""

    logging.info("Récupération des données de la carte...")
    data = get_map_data()
    logging.info(f"Données récupérées.")

    map_instance = create_map()

    logging.info("Ajout des données à la carte...")
    map_instance = populate_map(map_instance, data)
    logging.info("Données ajoutées.")

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
    # Ajout des couches de données
    for layer in data["layers"].values():
        map_layer = folium.FeatureGroup(name=layer["name"], show=layer["shown_by_default"])
        for zone in layer["zones"]:
            geojson(zone, layer["min_price"], layer["max_price"], COLORS).add_to(map_layer)
        map_instance.add_child(map_layer)

    folium.LayerControl().add_to(map_instance)

    return map_instance

def get_fill_color(zone_price, min_price, max_price, colors):
    """Calcule la couleur de remplissage d'une zone en fonction de son prix."""
    if min_price == max_price:  # Évite la division par zéro
        return colors[-1]
    normalized_price = (zone_price - min_price) / (max_price - min_price)
    return colors[int(normalized_price * (len(colors) - 1))]

def geojson(zone, min_price, max_price, colors):
    """Retourne un objet GeoJson configuré pour une zone donnée."""
    return folium.GeoJson(
        data=wkt.loads(zone["geom_wkt"]).__geo_interface__,
        style_function=lambda feature: {
            'fillColor': get_fill_color(zone["price"], min_price, max_price, colors),
            'color': 'white',
            'weight': 1,
            'fillOpacity': 0.5
        },
        tooltip=zone["name"]
    )
