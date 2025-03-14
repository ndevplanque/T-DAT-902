import os
from flask import send_file

def map():
    """Renvoie le contenu HTML de la carte."""
    return send_file(os.getenv('V1_MAP_FILEPATH'))
