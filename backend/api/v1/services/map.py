import os
from dotenv import load_dotenv
from flask import send_file

load_dotenv()
V1_MAP_FILEPATH = os.getenv('V1_MAP_FILEPATH')

def map():
    """Renvoie le contenu HTML de la carte."""
    return send_file(V1_MAP_FILEPATH)
