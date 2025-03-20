import streamlit as st

def Map(html_map):
    st.components.v1.html(html_map, height=600, scrolling=True)
