import streamlit as st
from utils import api
from components.WordCloud import WordCloud

st.title("Nuage de Mots 🌧️")

data = api.v1_word_cloud("cities", 123)
if data is not None:
    WordCloud(data)
else:
    st.error("Impossible de récupérer les données.")