import streamlit as st
import plotly.express as px
import pandas as pd

# Données d'analyse de sentiment
sentiments = {
    "positif": 19,
    "neutre": 2,
    "negatif": 0,
    "positif_percent": 90.5,
    "neutre_percent": 9.5,
    "negatif_percent": 0
}

# Création du DataFrame pour le graphique
data = pd.DataFrame({
    "Sentiment": ["Positif", "Neutre", "Négatif"],
    "Valeurs": [sentiments["positif"], sentiments["neutre"], sentiments["negatif"]],
    "Pourcentage": [sentiments["positif_percent"], sentiments["neutre_percent"], sentiments["negatif_percent"]]
})

# Configuration de l'interface Streamlit
st.title("Analyse des Sentiments")

# Graphique en anneau (Donut Chart)
fig = px.pie(data,
             names="Sentiment",
             values="Valeurs",
             hole=0.4,
             color="Sentiment",
             color_discrete_map={"Positif": "green", "Neutre": "gray", "Négatif": "red"},
             title="Répartition des Sentiments")

st.plotly_chart(fig)
