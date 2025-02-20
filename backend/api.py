from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/v1/health', methods=['GET'])
def api_v1_health():
    return jsonify({"success": True})

@app.route('/api/v1/data', methods=['GET'])
def api_v1_data():
    return jsonify({"message": "Hello from Flask!", "value": 42})

if __name__ == '__main__':
     app.run(debug=True, host='0.0.0.0', port=5000)  # L'API tourne sur localhost:5000
