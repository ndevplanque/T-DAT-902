import streamlit as st
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.graph_objects as go

def AreaDetails(item, area_details, area_transactions):
    st.write("---")
    st.subheader(f"Notes de {item['name']}")

    st.write(f"Résultats basés sur {area_details['rating']['count']} avis")
    grades = area_details["rating"]["grades"]

    educ, envi, secu, spor, life = st.columns(5, border=True)
    educ.markdown(f"<div style='text-align: center;'><p>Éducation</p><p style='font-size: 36px'>{grades['education']}</p></div>", unsafe_allow_html=True)
    envi.markdown(f"<div style='text-align: center;'><p>Environnement</p><p style='font-size: 36px'>{grades['environnement']}</p></div>", unsafe_allow_html=True)
    secu.markdown(f"<div style='text-align: center;'><p>Sécurité</p><p style='font-size: 36px'>{grades['securite']}</p></div>", unsafe_allow_html=True)
    spor.markdown(f"<div style='text-align: center;'><p>Sport & Loisirs</p><p style='font-size: 36px'>{grades['sport_loisir']}</p></div>", unsafe_allow_html=True)
    life.markdown(f"<div style='text-align: center;'><p>Vie Pratique</p><p style='font-size: 36px'>{grades['vie_pratique']}</p></div>", unsafe_allow_html=True)

    st.write("---")

    sentiments_fig = build_sentiments_fig(area_details['sentiments'])
    wordcloud_fig = build_wordcloud_fig(area_details['word_frequencies'])

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("Analyse des sentiments")
        st.plotly_chart(sentiments_fig)

    with col2:
        st.subheader("Nuage de mots")
        st.pyplot(wordcloud_fig)

    st.write("---")
    st.subheader("Transactions Immobilières")
    st.write(area_transactions)

def build_wordcloud_fig(data):
    # Générer le word cloud
    wc = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(data)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    return fig

def build_sentiments_fig(data):
    # Traduction des clés en labels
    chart_keys = ["positif", "neutre", "negatif"]
    translations = {
        "positif": "Positif",
        "neutre": "Neutre",
        "negatif": "Négatif"
    }

    # Vérification de la présence de données pour chaque label
    if not data or not all(key in data for key in chart_keys):
        raise ValueError("Données invalides.")

    # Calcul des labels, valeurs et couleurs
    labels = [translations[key] for key in chart_keys]
    values = [data[key] for key in chart_keys]
    colors = ["green", "gray", "red"]

    # Création du donut chart avec Plotly
    return go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.5,  # Pour faire un "donut"
        marker=dict(colors=colors),
        hoverinfo="label+percent+value",
        textinfo='label+percent'
    )])
