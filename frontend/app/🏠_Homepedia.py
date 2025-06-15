import os
import streamlit as st
from utils import api

# Configuration de la page principale
st.set_page_config(page_icon="🏠")

st.title("Homepedia 🏠")

if api.v1_health()["success"]:
    st.write("Statut : en ligne ✅")
else:
    st.error("Statut : hors-ligne ❌")

st.write("Choisissez une page dans le menu latéral pour commencer.")