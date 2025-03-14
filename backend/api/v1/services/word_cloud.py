from flask import jsonify
import json
import api.v1.repositories.word_cloud as repository

def word_cloud(entity, id):
    if entity not in ["cities", "departments", "regions"]:
        raise ValueError("Les nuages de mots ne sont disponibles que pour les 'cities', 'departments' ou 'regions'")

    return repository.get_word_cloud(entity, id)
