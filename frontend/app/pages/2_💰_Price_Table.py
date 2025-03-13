import streamlit as st
from utils import cache
from components.LayerTable import LayerTable

st.title("Tableau des Prix Immobiliers 💰")

try:
    map_data = cache.get_map_data()
    if map_data is not None:
        LayerTable(map_data)
    else:
        st.error("Impossible de récupérer les données.")
except RuntimeError as e:
    st.error(f"Erreur : {str(e)}")  # Afficher proprement l'erreur sans crasher l'UI
