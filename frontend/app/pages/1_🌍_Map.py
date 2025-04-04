import os
import streamlit as st
import streamlit.components.v1 as components

# Mettre la page en très large
st.set_page_config(layout="wide")

st.title("Carte des Prix Immobiliers 🌍")

# Lire le fichier HTML avec la carte Leaflet
with open('app/utils/map.html', 'r') as file:
    html_content = file.read()

# Afficher le fichier HTML dans Streamlit
components.html(html_content, height=600)