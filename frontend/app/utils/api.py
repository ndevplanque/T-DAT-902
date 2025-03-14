import os
from dotenv import load_dotenv
import streamlit as st
import requests

load_dotenv()

def v1(endpoint):
    return _api_v1(endpoint)

def _api_v1(endpoint):
    url = os.getenv('API_V1_URL')
    return f"{url}/{endpoint}"

def v1_map():
    """Récupère la carte HTML depuis l'API et retourne son contenu sous forme de texte."""
    response = requests.get(_api_v1("map"))
    if response.status_code == 200:
        return response.text  # Retourne directement le HTML
    return None

def v1_price_tables():
    response = requests.get(_api_v1("price-tables"))
    if response.status_code == 200:
        return response.json()
    return None

def v1_word_cloud(entity, id):
    response = requests.get(v1(f"word-cloud/{entity}/{id}"))
    if response.status_code == 200:
        return response.json()
    return None

def v1_health():
    response = requests.get(_api_v1("health"))
    if response.status_code == 200:
        return response.json()
    return None
