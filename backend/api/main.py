from flask import Flask, jsonify
import pandas as pd
import numpy as np
from api.v1.services.health import health as v1_health
from api.v1.services.example import example as v1_example
from api.v1.services.map import map as v1_map

app = Flask(__name__)

@app.route('/', methods=['GET'])
def root():
    return "Welcome to Homepedia API"

@app.route('/api/v1/health', methods=['GET'])
def api_v1_health():
    return jsonify(v1_health())

@app.route('/api/v1/example', methods=['GET'])
def api_v1_example():
    return jsonify(v1_example())

@app.route('/api/v1/map', methods=['GET'])
def api_v1_map():
    try:
        return jsonify(v1_map())
    except ValueError as e:
        return jsonify({"error": str(e)}), 404  # Retourne une 404 avec le message d'erreur

# Handler générique pour les erreurs
@app.errorhandler(Exception)
def handle_exception(e):
    error_name = str(e)
    error_code = str(e).split(" ")[0]
    if error_code.isdigit():
        error_code = int(error_code)
        error_name = error_name.split(":", 1)[0].split(" ", 1)[1].strip()
    else:
        error_code = 500
    return jsonify({"error": error_name, "code": error_code}), error_code
