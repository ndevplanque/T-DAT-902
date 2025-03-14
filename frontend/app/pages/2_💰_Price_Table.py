import streamlit as st
from utils import cache
from components.PriceTable import PriceTable

st.title("Tableau des Prix Immobiliers 💰")

try:
    prices_data = cache.get_prices_data()
    if prices_data is not None:
        PriceTable(prices_data)
    else:
        st.error("Impossible de récupérer les données.")
except RuntimeError as e:
    st.error(f"Erreur : {str(e)}")  # Afficher proprement l'erreur sans crasher l'UI
