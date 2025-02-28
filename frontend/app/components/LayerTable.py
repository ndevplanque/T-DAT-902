import streamlit as st
import pandas as pd

def LayerTable(data):
    """
    Affiche un tableau interactif par layer avec la possibilité de les ouvrir et fermer.

    :param data: Dictionnaire contenant les couches de zones avec leurs prix.
    """
    if not data or "layers" not in data:
        st.error("Données invalides ou indisponibles.")
        return

    for layer in data["layers"]:
        with st.expander(f"📍 {layer['name']} (Min: {layer['min_price']}€ | Max: {layer['max_price']}€)", expanded=False):
            # Transformation des données en DataFrame
            data_list = [{
                "Zone": zone["name"],
                "Prix (€/m²)": zone["price"]
            } for zone in layer["zones"]]

            df = pd.DataFrame(data_list)

            # Affichage du tableau interactif
            st.dataframe(df, use_container_width=True)
