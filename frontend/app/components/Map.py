import streamlit as st
import os
import folium
import requests
from utils import api
from streamlit_folium import folium_static

map_instance = None

def Map(data):
    _create()
    for layer in data["layers"]:
        _add_layer(layer)
    _activate_layer_control()
    _display()

def _create():
    global map_instance
    map_instance = folium.Map(
        location=[48.584614, 7.750713],  # Strasbourg
        zoom_start=10,
        tiles=None # Désactive le fond de carte par défaut (OpenStreetMap)
    )

    # Ajout de la couche Mapbox comme TileLayer
    token = os.getenv('MAPBOX_ACCESS_TOKEN')
    folium.TileLayer(
        tiles=f"https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/{{z}}/{{x}}/{{y}}?access_token={token}",
        attr="Mapbox",
        name="Carte Mapbox",
        overlay=False,
        control=False
    ).add_to(map_instance)

# Utilisation d'une échelle de couleurs douces, du vert au rouge
colors = ["#060", "#282", "#3C3", "#7F0", "#AF2", "#FF0", "#FD0", "#FA0", "#F80", "#F64", "#F40", "#F00"]

def _get_fill_color(zone, min_price, max_price):
    normalized_price = (zone["price"] - min_price) / (max_price - min_price)
    index = int(normalized_price * (len(colors) - 1))
    return colors[index]

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

def _add_layer(layer):
    map_layer = folium.FeatureGroup(name=layer["name"])

    for zone in layer["zones"]:
        color = _get_fill_color(zone, layer["min_price"], layer["max_price"])
        polygon = _polygon(zone, color)
        map_layer.add_child(polygon)

    global map_instance
    map_instance.add_child(map_layer)

def _activate_layer_control():
    global map_instance
    if map_instance is None:
            raise ValueError("La carte doit être créée avant d'activer le contrôle des couches.")
    folium.LayerControl().add_to(map_instance)

def _display():
    global map_instance
    if map_instance is None:
        raise ValueError("La carte doit être créée avant d'être affichée.")
    folium_static(map_instance)
