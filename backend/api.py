from flask import Flask, jsonify
import pandas as pd
import numpy as np

app = Flask(__name__)

@app.route('/', methods=['GET'])
def root():
    return api_v1_health()

@app.route('/api/v1/health', methods=['GET'])
def api_v1_health():
    return jsonify({"success": True})

@app.route('/api/v1/data', methods=['GET'])
def api_v1_data():
    return jsonify({"message": "Hello from Flask!", "value": 42})

@app.route('/api/v1/map', methods=['GET'])
def api_v1_map():
    df = pd.DataFrame(
        {
            "lat": np.random.randn(1000) / 50 + 37.76,
            "lon": np.random.randn(1000) / 50 + -122.4,
            "size": np.random.randn(1000) * 100,
            "color": np.random.rand(1000, 4).tolist(),
        }
    )
    return jsonify(df.to_dict(orient="records"))