import streamlit as st
from utils import api

@st.cache_data
def get_map_data():
    """Met en cache uniquement si la requête réussit."""
    data = api.v1_map()
    if data is not None:
        return data
    else:
        raise RuntimeError("Échec de la récupération de la carte")  # Empêche le cache sur un échec

@st.cache_data
def get_prices_data():
    """Met en cache uniquement si la requête réussit."""
    data = api.v1_price_table()
    if data is not None:
        return data
    else:
        raise RuntimeError("Échec de la récupération de la carte")  # Empêche le cache sur un échec
