import os
import streamlit as st
from utils import api

# Configuration de la page principale
st.set_page_config(page_icon="🏠")

st.title("Homepedia 🏠")

if api.v1_health()["success"]:
    st.write("API Flask : Online ✅")
else:
    st.error("API Flask : Offline ❌")
