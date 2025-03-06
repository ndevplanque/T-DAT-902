from flask import jsonify
import json
import api.v1.repositories.map as repository

def map():
    cities = repository.get_cities()
    if "zones" in cities and isinstance(cities["zones"], list) and not cities["zones"]:
        raise ValueError("Erreur : La liste 'cities' est vide.")

    departments = repository.get_departments()
    if "zones" in departments and isinstance(departments["zones"], list) and not departments["zones"]:
        raise ValueError("Erreur : La liste 'departments' est vide.")

    regions = repository.get_regions()
    if "zones" in regions and isinstance(regions["zones"], list) and not regions["zones"]:
        raise ValueError("Erreur : La liste 'regions' est vide.")

    return {"layers": {
        "cities": cities,
        "departments": departments,
        "regions": regions,
    }}
