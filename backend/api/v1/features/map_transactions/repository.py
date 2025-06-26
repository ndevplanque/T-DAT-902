import v1.database.queries as q
import json
from v1.database.postgres import Postgres
from v1.models.bounds import Bounds


def get_transactions(bounds: Bounds):
    features = []

    query = q.list_map_transactions(bounds)

    db = Postgres()
    for date_mutation, valeur_fonciere, surface_reelle_bati, surface_terrain, geo_json in db.fetchall(query):
        features.append({
            "type": "Feature",
            "properties": {
                "date_mutation": date_mutation,
                "val_fonciere": valeur_fonciere,
                "surface_m2": surface_reelle_bati,
                "terrain_m2": surface_terrain,
            },
            "geometry": json.loads(geo_json)
        })

    db.close()

    return {
        "type": "FeatureCollection",
        "features": features,
    }
