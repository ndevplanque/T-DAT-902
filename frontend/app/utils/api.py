import os
import streamlit as st
import requests

def v1(endpoint):
    return _api_v1(endpoint)

def _api_v1(endpoint):
    url = os.getenv('API_V1_URL')
    return f"{url}/{endpoint}"

@st.cache_data
def v1_map():
    response = requests.get(_api_v1("map"))
    if response.status_code == 200:
        return response.json()
    return None

def v1_health():
    response = requests.get(_api_v1("health"))
    if response.status_code == 200:
        return response.json()
    return None
