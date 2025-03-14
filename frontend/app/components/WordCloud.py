import streamlit as st
import wordcloud as wc
import matplotlib.pyplot as plt

def WordCloud(data):
    if not data or not all(isinstance(data.get(key), int) for key in data):
        raise ValueError("Données invalides.")

    word_cloud = wc.WordCloud(width=800, height=400, background_color="white").generate_from_frequencies(data)

    fig, ax = plt.subplots()
    ax.imshow(word_cloud, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)
