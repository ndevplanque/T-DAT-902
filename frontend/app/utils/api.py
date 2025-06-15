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


def v1_area_listing():
    response = requests.get(_api_v1("area-listing"))
    if response.status_code == 200:
        return response.json()
    return None


def v1_area_details(entity, id):
    response = requests.get(_api_v1(f"area-details/{entity}/{id}"))
    if response.status_code == 200:
        return response.json()
    return None


def v1_area_transactions(entity, id):
    response = requests.get(_api_v1(f"area-transactions/{entity}/{id}"))
    if response.status_code == 200:
        return response.json()
    return None

