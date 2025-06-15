from v1.database.mongodb import MongoDB
import logs


def get_cities_area_details(id):
    """Retourne des données plus poussées pour une entité donnée"""

    area_details = {
        'word_frequencies': {},
        'sentiments': {},
        'rating': {
            'grades': {},
            'count': 0
        }
    }

    with MongoDB() as db:

        city = db.find_one(
            collection='villes',
            query={'city_id': id},
            fields=MongoDB.only_fields(['notes', 'nombre_avis'])
        )

        aggregates = db.find_one(
            collection='mots_villes',
            query={'city_id': id},
            fields=MongoDB.only_fields(['mots', 'sentiments'])
        )

        # Si la ville ou les aggregats ne sont pas trouvés, fallback sur tout à zéro
        if city is None or aggregates is None:
            logs.info(f"Données manquantes pour city_id: {id}")
            return area_details

        # Placer les notes et le nombre d'avis dans rating
        area_details['rating'] = {
            'grades': city.get('notes', {}),
            'count': city.get('nombre_avis', 0)
        }

        # Convertir l'array des mots en dictionnaire {"parc": 5, "école": 3} etc.
        wf = {}
        if aggregates and 'mots' in aggregates:
            for item in aggregates['mots']:
                wf[item['mot']] = item['poids']
        area_details['word_frequencies'] = wf

        # Les sentiments sont déjà dans le bon format
        area_details['sentiments'] = aggregates.get('sentiments', {})

    return area_details
