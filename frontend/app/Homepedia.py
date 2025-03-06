import os
import streamlit as st
import requests
from dotenv import load_dotenv
from utils import api
from utils import cache
from components.Map import Map
from components.LayerTable import LayerTable

# Configuration de la page principale
st.set_page_config(
    page_icon="🏠"
)

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

st.title("Homepedia 🏠")

if api.v1_health()["success"]:
    st.write("API Flask : Online ✅")
else:
    st.error("API Flask : Offline ❌")

st.title("Carte des Prix Immobiliers 📍")

try:
    map_data = cache.get_map_data()
    if map_data is not None:
        Map(map_data)
        LayerTable(map_data)
    else:
        st.error("Impossible de récupérer les données.")
except RuntimeError as e:
    st.error(f"Erreur : {str(e)}")  # Afficher proprement l'erreur sans crasher l'UI
