import streamlit as st
import requests
import pandas as pd

API_V1_URL = "http://backend:5000/api/v1"

def v1(endpoint):
    return f"{API_V1_URL}/{endpoint}"

st.title("Homepedia 🏠")

health = requests.get(v1("health"))
if health.status_code == 200:
    st.write("API Flask : Online ✅")
else:
    st.error("API Flask : Offline ❌")

if st.button("Fetch data"):
    response = requests.get(v1("data"))
    if response.status_code == 200:
        data = response.json()
        st.write(f"Message : {data['message']}")
        st.write(f"Value : {data['value']}")
    else:
        st.error("Error fetching data.")

st.title("Visualisation de la carte")

map = requests.get(v1("map"))
if map.status_code == 200:
    st.map(pd.DataFrame(map.json()), latitude="lat", longitude="lon", size="size", color="color")
else:
    st.error("Error fetching map data.")