import streamlit as st
import requests

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
