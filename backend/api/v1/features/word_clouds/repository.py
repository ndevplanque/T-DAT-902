from v1.database.mongodb import MongoDB


def get_word_frequencies(entity, id):
    """Retourne un nuage de mots pour une entité donnée"""

    if entity != 'cities':
        raise AttributeError("Les nuages de mots ne sont disponibles que pour les 'cities'")

    with MongoDB() as db:
        document = db.find_one(
            collection='mots_villes',
            query={'city_id': id},
            fields=MongoDB.only_fields(['mots'])
        )
        frequencies = {}
        if document and 'mots' in document:
            for item in document['mots']:
                frequencies[item['mot']] = item['poids']
        return frequencies
