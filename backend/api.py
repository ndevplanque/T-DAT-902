from flask import Flask, jsonify
import pandas as pd
import numpy as np
from v1.services.health import health
from v1.services.example import example
from v1.services.map import map

app = Flask(__name__)

@app.route('/', methods=['GET'])
def root():
    return "Welcome to Homepedia API"

@app.route('/api/v1/health', methods=['GET'])
def api_v1_health():
    return jsonify(health())

@app.route('/api/v1/example', methods=['GET'])
def api_v1_example():
    return jsonify(example())

@app.route('/api/v1/map', methods=['GET'])
def api_v1_map():
    return jsonify(map())
