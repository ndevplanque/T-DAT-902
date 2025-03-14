import streamlit as st
from utils import cache
from components.PriceTable import PriceTable

st.title("Tableau des Prix Immobiliers 💰")

try:
    data = cache.get_price_tables()
    if not data or "price_tables" not in data:
        raise RuntimeError("Données invalides ou indisponibles.")

    for table in data["price_tables"]:
        if table is not None:
            PriceTable(table)
        else:
            st.error("Impossible de récupérer les données.")
except RuntimeError as e:
    st.error(f"Erreur : {str(e)}")  # Afficher proprement l'erreur sans crasher l'UI
