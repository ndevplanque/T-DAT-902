import streamlit as st
import pandas as pd

def PriceTable(data):
    with st.expander(f"📍 {data['title']} (Min: {data['aggs']['min_price']}€ | Max: {data['aggs']['max_price']}€)", expanded=False):
        # Transformation des données en DataFrame
        data_list = [{
            "Zone": zone["name"],
            "Prix (€/m²)": zone["price"]
        } for zone in data["items"]]

        df = pd.DataFrame(data_list)

        # Affichage du tableau interactif
        st.dataframe(df, use_container_width=True)
