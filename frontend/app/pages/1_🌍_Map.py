import os
import streamlit as st
from utils import api
from components.Map import Map

st.title("Carte des Prix Immobiliers 🌍")

html_map = api.v1_map()
if html_map:
    Map(html_map)
else:
    st.error("Impossible de charger la carte.")
