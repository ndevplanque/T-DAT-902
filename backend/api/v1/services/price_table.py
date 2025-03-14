from flask import jsonify
import json
import api.v1.repositories.price_table as repository

def price_table():
    cities = repository.get_cities_prices()
    if "zones" in cities and isinstance(cities["zones"], list) and not cities["zones"]:
        raise ValueError("Erreur : La liste 'cities' est vide.")

    departments = repository.get_departments_prices()
    if "zones" in departments and isinstance(departments["zones"], list) and not departments["zones"]:
        raise ValueError("Erreur : La liste 'departments' est vide.")

    regions = repository.get_regions_prices()
    if "zones" in regions and isinstance(regions["zones"], list) and not regions["zones"]:
        raise ValueError("Erreur : La liste 'regions' est vide.")

    return {
        "price_table": {
            "cities": cities,
            "departments": departments,
            "regions": regions,
        }
    }
