import streamlit as st
from utils import api

@st.cache_data
def get_price_tables():
    """Met en cache uniquement si la requête réussit."""
    data = api.v1_price_tables()
    if data is not None:
        return data
    else:
        raise RuntimeError("Échec de la récupération de la carte")  # Empêche le cache sur un échec
