import streamlit as st
from utils import cache, api
from components.PriceTable import PriceTable
from components.AreaDetails import AreaDetails

st.set_page_config(layout="wide")

st.title("Comparatif des Prix Immobiliers 💰")

try:
    areas = cache.get_area_listing()
    entities = ['cities']  # ['regions', 'departments', 'cities']

    # Vérification de la validité des données
    if not areas or not all(entity in areas for entity in entities):
        raise RuntimeError("Données invalides ou indisponibles.")

    option = st.selectbox(
        label="Choix de la localité",
        options=[
            f"{item['name']} ({item['id']})"
            for entity in entities
            for item in areas[entity]['items']
        ],
        index=None,
        placeholder="Strasbourg...",
    )

    if option is not None:
        # Extraction de l'ID et de la localité sélectionnée
        selected_name = option.split(" (")[0].strip()
        selected_id = option.split(" (")[1].strip("()")

        # Récupération des détails de la localité
        for entity in entities:
            for item in areas[entity]['items']:
                if item["id"] == selected_id and item["name"] == selected_name:
                    area_transactions = api.v1_area_transactions(entity, item["id"])
                    area_details = api.v1_area_details(entity, item["id"])
                    AreaDetails(item, area_details, area_transactions)
                    break
    else:
        # Sinon, on affiche le listing des prix par type de localité
        st.subheader("Pour la France entière")
        for entity in entities:
            PriceTable(areas[entity])
except RuntimeError as e:
    st.error(f"Erreur : {str(e)}")  # Afficher proprement l'erreur sans crasher l'UI
