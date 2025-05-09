from v1.database.mongodb import MongoDB


def schema():
    """Retourne le schéma de la base de données"""
    with MongoDB() as db:
        return db.schema()
