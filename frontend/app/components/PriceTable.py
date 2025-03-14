import streamlit as st
import pandas as pd

def PriceTable(data):
    """ Affiche un tableau interactif des prix immobiliers. """
    if not data or "price_table" not in data:
        st.error("Données invalides ou indisponibles.")
        return

    for key in data["price_table"]:
        table = data["price_table"][key]
        with st.expander(f"📍 {table['title']} (Min: {layer['aggs']['min']}€ | Max: {layer['aggs']['max']}€)", expanded=False):
            # Transformation des données en DataFrame
            data_list = [{
                "Zone": zone["name"],
                "Prix (€/m²)": zone["price"]
            } for zone in layer["items"]]

            df = pd.DataFrame(data_list)

            # Affichage du tableau interactif
            st.dataframe(df, use_container_width=True)
