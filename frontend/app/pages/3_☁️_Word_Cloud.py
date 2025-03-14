import streamlit as st
from utils import api

st.title("Nuage de Mots 🌧️")

image = api.v1_word_cloud("cities", 123)
if image is not None:
    st.write(image)
else:
    st.error("Impossible de récupérer les données.")
