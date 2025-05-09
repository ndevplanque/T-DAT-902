import logs
from flask import Flask, jsonify
from flask_cors import CORS
from v1.models.bounds import Bounds
from v1.features.health.service import health as v1_health
from v1.features.map_areas.service import map_areas as v1_map_areas
from v1.features.price_tables.service import price_tables as v1_price_tables
from v1.features.word_clouds.service import word_clouds as v1_word_clouds
from v1.features.sentiments.service import sentiments as v1_sentiments
from v1.features.area_details.service import area_details as v1_area_details
import v1.features.databases.service as databases

# Configuration de l'application Flask
logs.info("Starting Homepedia API")
app = Flask(__name__)
logs.info("Started")
CORS(app)  # La map est exécutée côté client donc on doit autoriser les requêtes CORS
logs.info("CORS enabled")


@app.route('/', methods=['GET'])
def root():
    return "Welcome to Homepedia API"


@app.route('/api/v1/health', methods=['GET'])
def api_v1_health():
    return v1_health()


@app.route('/api/v1/map-areas/<zoom>/<sw_lat>/<sw_lon>/<ne_lat>/<ne_lon>', methods=['GET'])
def api_v1_map_areas(zoom, sw_lat, sw_lon, ne_lat, ne_lon):
    bounds = Bounds(int(zoom), float(sw_lat), float(sw_lon), float(ne_lat), float(ne_lon))
    logs.info(f"Bounds: {bounds}")
    return v1_map_areas(bounds)


@app.route('/api/v1/price-tables', methods=['GET'])
def api_v1_price_tables():
    return v1_price_tables()


@app.route('/api/v1/sentiments/<entity>/<id>', methods=['GET'])
def api_v1_sentiments(entity, id):
    return v1_sentiments(entity, id)


@app.route('/api/v1/word-clouds/<entity>/<id>', methods=['GET'])
def api_v1_word_clouds(entity, id):
    return v1_word_clouds(entity, id)


@app.route('/api/v1/area-details/<entity>/<id>', methods=['GET'])
def api_v1_area_details(entity, id):
    return v1_area_details(entity, id)


@app.route('/api/v1/mongodb/schema', methods=['GET'])
def api_v1_mongodb_schema():
    return databases.mongodb_schema()


@app.route('/api/v1/postgres/schema', methods=['GET'])
def api_v1_postgres_schema():
    return databases.postgres_schema()


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
