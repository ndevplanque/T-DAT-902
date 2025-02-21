from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/v1/health', methods=['GET'])
def api_v1_health():
    return jsonify({"success": True})

@app.route('/api/v1/data', methods=['GET'])
def api_v1_data():
    return jsonify({"message": "Hello from Flask!", "value": 42})
