import streamlit as st
import pandas as pd

def PriceTable(data):
    """ Affiche un tableau interactif des prix immobiliers. """
    if not data or "price_tables" not in data:
        st.error("Données invalides ou indisponibles.")
        return

    for table in data["price_tables"]:
        with st.expander(f"📍 {table['title']} (Min: {table['aggs']['min_price']}€ | Max: {table['aggs']['max_price']}€)", expanded=False):
            # Transformation des données en DataFrame
            data_list = [{
                "Zone": zone["name"],
                "Prix (€/m²)": zone["price"]
            } for zone in table["items"]]

            df = pd.DataFrame(data_list)

            # Affichage du tableau interactif
            st.dataframe(df, use_container_width=True)
