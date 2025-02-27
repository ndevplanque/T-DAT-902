import streamlit as st
import os
import folium
import requests
from utils import api
from streamlit_folium import folium_static

map_instance = None

def Map(data):
    _create() # Création de la carte avec Mapbox
    _add_zones(data) # Ajout des zones sur la carte
    _display() # Affichage de la carte

def _create():
    token = os.getenv('MAPBOX_ACCESS_TOKEN')
    global map_instance
    map_instance = folium.Map(
       location=[48.584614, 7.750713], # Strasbourg
       zoom_start=10,
       tiles=f"https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/{{z}}/{{x}}/{{y}}?access_token={token}",
       attr='Mapbox',
    )

# Utilisation d'une échelle de couleurs douces, du vert au rouge
colors = [
    "#006400",  # Vert foncé
    "#228B22",  # Vert forêt
    "#32CD32",  # Vert lime
    "#7CFC00",  # Vert clair
    "#ADFF2F",  # Vert jaune
    "#FFFF00",  # Jaune
    "#FFD700",  # Jaune doré
    "#FFA500",  # Orange
    "#FF8C00",  # Orange foncé
    "#FF6347",  # Tomate
    "#FF4500",  # Rouge orangé
    "#FF0000"   # Rouge
]

def _get_fill_color(zone, min_price, max_price):
    # Calcul de la position relative entre le prix min et max
    normalized_price = (zone["price"] - min_price) / (max_price - min_price)

    # Sélection de la couleur correspondante
    return colors[int(normalized_price * (len(colors) - 1))]

def _polygon(zone, color):
    return folium.Polygon(
        locations=zone["coordinates"],
        color="white",
        weight=1,
        fill=True,
        fill_color=color,
        fill_opacity=0.3,
        popup=zone["name"]
    )

# Ajouter des zones sur la carte
def _add_zones(map_data):
    global map_instance
    if map_instance is None:
        raise ValueError("La carte doit être créée avant d'ajouter des zones.")

    zones = map_data["zones"]
    min_price = map_data["min_price"]
    max_price = map_data["max_price"]

    for zone in zones:
        color = _get_fill_color(zone, min_price, max_price)
        _polygon(zone, color).add_to(map_instance)

# Affichage de la carte
def _display():
    global map_instance
    if map_instance is None:
        raise ValueError("La carte doit être créée avant d'être affichée.")

    folium_static(map_instance)