from v1.database.mongodb import MongoDB
from v1.database.postgres import Postgres

def mongodb_schema():
    """Retourne le schéma de la base de données"""
    with MongoDB() as db:
        return db.schema()

def postgres_schema():
    """Retourne le schéma de la base de données"""
    db = Postgres()
    schema = db.schema()
    return schema
