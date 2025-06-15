import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime


def AreaDetails(item, area_details, area_transactions):
    st.write("---")
    st.subheader(f"Notes de {item['name']}")

    st.write(f"Résultats basés sur {area_details['rating']['count']} avis")

    grades = area_details["rating"]["grades"] if "rating" in area_details and "grades" in area_details["rating"] else {}

    g_education = grades['education'] if 'education' in grades else 0
    g_environnement = grades['environnement'] if 'environnement' in grades else 0
    g_securite = grades['securite'] if 'securite' in grades else 0
    g_sport_loisir = grades['sport_loisir'] if 'sport_loisir' in grades else 0
    g_vie_pratique = grades['vie_pratique'] if 'vie_pratique' in grades else 0

    educ, envi, secu, spor, life = st.columns(5, border=True)

    educ.markdown(
        f"<div style='text-align: center;'><p>Éducation</p><p style='font-size: 36px'>{g_education}</p></div>",
        unsafe_allow_html=True)
    envi.markdown(
        f"<div style='text-align: center;'><p>Environnement</p><p style='font-size: 36px'>{g_environnement}</p></div>",
        unsafe_allow_html=True)
    secu.markdown(
        f"<div style='text-align: center;'><p>Sécurité</p><p style='font-size: 36px'>{g_securite}</p></div>",
        unsafe_allow_html=True)
    spor.markdown(
        f"<div style='text-align: center;'><p>Sport & Loisirs</p><p style='font-size: 36px'>{g_sport_loisir}</p></div>",
        unsafe_allow_html=True)
    life.markdown(
        f"<div style='text-align: center;'><p>Vie Pratique</p><p style='font-size: 36px'>{g_vie_pratique}</p></div>",
        unsafe_allow_html=True)

    st.write("---")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("Analyse des sentiments")
        if 'sentiments' not in area_details or area_details['sentiments'] == {}:
            st.write("Aucun sentiment disponible pour cette localité.")
        else:
            sentiments_fig = build_sentiments_fig(area_details['sentiments'])
            st.plotly_chart(sentiments_fig)

    with col2:
        st.subheader("Nuage de mots")
        if 'word_frequencies' not in area_details or area_details['word_frequencies'] == {}:
            st.write("Aucun mot disponible pour cette localité.")
        else:
            wordcloud_fig = build_wordcloud_fig(area_details['word_frequencies'])
            st.pyplot(wordcloud_fig)

    st.write("---")
    st.subheader("Transactions Immobilières")

    nb_transactions = 0
    if area_transactions and len(area_transactions) > 0:
        nb_transactions = len(area_transactions)

    with st.expander(f"{nb_transactions} transactions disponibles", expanded=(nb_transactions == 0)):
        if nb_transactions == 0:
            st.write("Aucune transaction immobilière disponible pour cette localité.")
            return

        data_list = [{
            "Date": transaction['date'],
            "Prix (€)": transaction["prix"],
            "Surface bâtiment (m2)": transaction["surface_batiment"],
            "Surface terrain (m2)": transaction["surface_terrain"]
        } for transaction in area_transactions]

        df = pd.DataFrame(data_list)

        df = df.sort_values(by='Date', ascending=True)

        # Affichage (la colonne "Date réelle" est utilisée pour le tri mais on ne l'affiche pas)
        st.dataframe(
            df[["Date", "Prix (€)", "Surface bâtiment (m2)", "Surface terrain (m2)"]],
            use_container_width=True,
            hide_index=True
        )


def build_wordcloud_fig(data):
    # Générer le word cloud
    wc = WordCloud(width=800, height=750, background_color='white').generate_from_frequencies(data)
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
