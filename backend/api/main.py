from dotenv import load_dotenv
from flask import Flask, jsonify
from api.v1.services.health import health as v1_health
from api.v1.services.example import example as v1_example
from api.v1.services.map import map as v1_map_html
from api.v1.services.price_tables import price_tables as v1_price_tables
from api.v1.services.word_cloud import word_cloud as v1_word_cloud

load_dotenv()
app = Flask(__name__)

@app.route('/', methods=['GET'])
def root():
    return "Welcome to Homepedia API"

@app.route('/api/v1/health', methods=['GET'])
def api_v1_health():
    return v1_health()

@app.route('/api/v1/example', methods=['GET'])
def api_v1_example():
    return v1_example()

@app.route('/api/v1/map', methods=['GET'])
def api_v1_map():
    return v1_map_html()

@app.route('/api/v1/price-tables', methods=['GET'])
def api_v1_price_table():
    return v1_price_tables()

@app.route('/api/v1/word-cloud/<entity>/<id>', methods=['GET'])
def api_v1_word_cloud(entity, id):
    return v1_word_cloud(entity, id)

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
