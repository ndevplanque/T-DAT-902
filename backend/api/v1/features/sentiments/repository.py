from v1.database.mongodb import MongoDB


def get_sentiments(entity, id):
    """Retourne les sentiments pour une entité donnée"""
    if entity != 'cities':
        raise AttributeError("Les sentiments ne sont disponibles que pour les 'cities'")

    with MongoDB() as db:
        document = db.find_one(
            collection='mots_villes',
            query={'city_id': id},
            fields=MongoDB.only_fields(['sentiments'])
        )
        if document and 'sentiments' in document:
            return document['sentiments']
        return {}
