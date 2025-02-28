# Librairies
import os
import streamlit as st
import pandas as pd
import requests
from dotenv import load_dotenv
import utils.api as api
from components.Map import Map

# Configuration de la page principale
st.set_page_config(
    page_icon="🏠"
)

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupération des données
health_response = requests.get(api.v1("health"))
map_response = requests.get(api.v1("map"))

# Affichage de l'état de l'API Flask
st.title("Homepedia 🏠")

if health_response.status_code == 200:
    st.write("API Flask : Online ✅")
else:
    st.error("API Flask : Offline ❌")

# Affichage de la carte
st.title("Carte des Prix Immobiliers 📍")

if map_response.status_code == 200:
    Map(map_response.json())
else:
    st.error("Impossible de récupérer les données")
