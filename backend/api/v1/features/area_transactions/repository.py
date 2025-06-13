from v1.database.postgres import Postgres
import v1.database.queries as q
import numpy as np
import logs
from datetime import datetime


def get_transactions(entity, ids):
    if entity != 'cities':
        raise AttributeError("Les transactions ne sont disponibles que pour les 'cities'")

    query = q.list_cities_properties(ids)

    db = Postgres()

    data = []

    for date_mutation, valeur_fonciere, surface_reelle_bati, surface_terrain in db.fetchall(query):
        # Filtrer les transactions avec des prix aberrants
        if valeur_fonciere is None or valeur_fonciere < 500:
            continue

        # S'assurer que date_mutation est un datetime, sinon le parser
        if isinstance(date_mutation, str):
            date_mutation = datetime.fromisoformat(date_mutation)

        # Formatage de la date
        date_formatted = date_mutation.strftime('%Y-%m-%d')

        data.append({
            'date': date_formatted,
            'prix': valeur_fonciere,
            'surface_batiment': surface_reelle_bati,
            'surface_terrain': surface_terrain,
        })

    db.close()

    return data
