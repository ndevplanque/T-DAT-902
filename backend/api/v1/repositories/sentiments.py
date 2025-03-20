from api.v1.database.postgres import Postgres

def get_sentiments(entity, id):
    return {
        "positif": 19,
        "neutre": 2,
        "negatif": 5
    }
