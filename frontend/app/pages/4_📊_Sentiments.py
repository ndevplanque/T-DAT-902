import streamlit as st
from utils import api

st.title("Sentiments 📊")

image = api.v1_sentiments("cities", 123)
if image is not None:
    st.write(image)
else:
    st.error("Impossible de récupérer les données.")
