from v1.database.mongodb import MongoDB


def get_area_details(entity, id):
    """Retourne des données plus poussées pour une entité donnée"""
    if entity != 'cities':
        raise AttributeError("Les détails ne sont disponibles que pour les 'cities'")

    details = {}

    with (MongoDB() as db):

        document = db.find_one(
            collection='mots_villes',
            query={'city_id': id},
            fields=MongoDB.only_fields(['mots', 'sentiments'])
        )

        wf = {}
        if document and 'mots' in document:
            for item in document['mots']:
                wf[item['mot']] = item['poids']
        details['word_frequencies'] = wf

        details['sentiments'] = document.get('sentiments', {})

        document = db.find_one(
            collection='villes',
            query={'city_id': id},
            fields=MongoDB.only_fields(['notes', 'nombre_avis'])
        )

        details['rating'] = {
            'grades': document.get('notes', {}),
            'count': document.get('nombre_avis', 0)
        }

    return details
