import streamlit as st
from utils import api

@st.cache_data
def get_area_listing():
    """Met en cache uniquement si la requête réussit."""
    areas = api.v1_area_listing()
    if areas is not None:
        return areas
    else:
        raise RuntimeError("Échec de la récupération des zones")  # Empêche le cache sur un échec
