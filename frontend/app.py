# Librairies
import os
from dotenv import load_dotenv
import streamlit as st
import requests
from streamlit_folium import folium_static
import pandas as pd

# Local
import map_utils as map
import api_utils as api

load_dotenv() # Charger les variables d'environnement depuis le fichier .env

st.title("Homepedia 🏠")

health = requests.get(api.v1("health"))
if health.status_code == 200:
    st.write("API Flask : Online ✅")
else:
    st.error("API Flask : Offline ❌")

if st.button("Fetch data"):
    response = requests.get(api.v1("data"))
    if response.status_code == 200:
        data = response.json()
        st.write(f"Message : {data['message']}")
        st.write(f"Value : {data['value']}")
    else:
        st.error("Error fetching data.")

st.title("Carte des Prix Immobiliers 📍")

response = requests.get(api.v1("map"))
if response.status_code == 200:
    data = response.json()
    m = map.create() # Création de la carte avec Mapbox

    # Ajouter des polygones représentant les zones
    for zone in data["zones"]:
        map.polygon(zone, data["min_price"], data["max_price"]).add_to(m)

    folium_static(m) # Affichage de la carte
else:
    st.error("Impossible de récupérer les données")
