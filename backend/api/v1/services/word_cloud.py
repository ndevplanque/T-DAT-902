from flask import jsonify
import json
import api.v1.repositories.word_cloud as repository

def word_cloud(entity, id):
    if entity not in ["cities", "departments", "regions"]:
            raise ValueError("Entity doit être 'cities', 'departments' ou 'regions'")

    return repository.word_cloud(entity, id)
