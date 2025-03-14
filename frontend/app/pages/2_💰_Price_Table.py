import streamlit as st
from utils import cache
from components.PriceTable import PriceTable

st.title("Tableau des Prix Immobiliers 💰")

try:
    price_tables = cache.get_price_tables()
    if price_tables is not None:
        PriceTable(price_tables)
    else:
        st.error("Impossible de récupérer les données.")
except RuntimeError as e:
    st.error(f"Erreur : {str(e)}")  # Afficher proprement l'erreur sans crasher l'UI
