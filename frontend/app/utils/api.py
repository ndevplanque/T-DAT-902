import os
from dotenv import load_dotenv
import streamlit as st
import requests
from io import BytesIO
from PIL import Image

load_dotenv()

def v1(endpoint):
    return _api_v1(endpoint)

def _api_v1(endpoint):
    url = os.getenv('API_URL')
    return f"{url}/api/v1/{endpoint}"

def v1_health():
    response = requests.get(_api_v1("health"))
    if response.status_code == 200:
        return response.json()
    return None

def v1_price_tables():
    response = requests.get(_api_v1("price-tables"))
    if response.status_code == 200:
        return response.json()
    return None

