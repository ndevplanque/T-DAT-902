import os
import streamlit as st
from dotenv import load_dotenv
from utils import api

# Configuration de la page principale
st.set_page_config(
    page_icon="🏠"
)

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

st.title("Homepedia 🏠")

if api.v1_health()["success"]:
    st.write("API Flask : Online ✅")
else:
    st.error("API Flask : Offline ❌")