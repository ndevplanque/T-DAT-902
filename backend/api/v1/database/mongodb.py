from typing import Any, Mapping

import logs
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from pymongo.synchronous.cursor import Cursor


class MongoDB:
    def __init__(self, uri="mongodb://root:rootpassword@host.docker.internal:27017", dbname="villes_france"):
        self.client = MongoClient(uri)
        self.db = self.client[dbname]

    def __enter__(self):
        """Permet d'utiliser `with MongoDB() as db`"""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Ferme proprement la connexion en fin d'utilisation"""
        self.close()

    def close(self):
        """Ferme la connexion au client MongoDB"""
        if self.client:
            self.client.close()

    def find(self, collection_name: str, only_fields: list = None, query: dict = None):
        """Exécute une requête pour récupérer tous les documents correspondant à la requête"""
        if only_fields is None:
            fields = {}
        else:
            fields = {field: 1 for field in only_fields}
            if "_id" not in fields:
                fields["_id"] = 0
        if query is None:
            query = {}
        try:
            collection = self.db[collection_name]
            return collection.find(query, fields)
        except PyMongoError as e:
            logs.info(f"Erreur MongoDB : {e}")
            return []

    def fields(self, collection_name: str):
        """Retourne les champs de la collection"""
        try:
            collection = self.db[collection_name]
            return list(collection.find_one().keys())
        except PyMongoError as e:
            logs.info(f"Erreur MongoDB : {e}")
            return None

    def collections(self):
        """Retourne les collections de la base de données"""
        try:
            return self.db.list_collection_names()
        except PyMongoError as e:
            logs.info(f"Erreur MongoDB : {e}")
            return []

    def schema(self):
        """Retourne le schéma de la base de données"""
        try:
            collections = {}
            for name in self.collections():
                sample_item = self.db[name].find_one()
                collections[name] = {"example": MongoDB.json(sample_item), "keys": {}}
                for key in self.fields(name):
                    collections[name]["keys"][key] = sample_item.get(key).__class__.__name__
            return {
                "db_name": self.db.name,
                "ok": self.db.command("dbstats")["ok"],
                "collections_count": len(self.collections()),
                "collections": collections,
                "size": self.db.command("dbstats")["dataSize"],
                "items": self.db.command("dbstats")["objects"],
            }
        except PyMongoError as e:
            logs.info(f"Erreur MongoDB : {e}")
            return None

    @staticmethod
    def json(data):
        """Convertit les données en JSON"""

        # Mapping correspond à un document seul
        # Cursor correspond à une liste de documents
        if not data or not isinstance(data, (Mapping, Cursor)):
            return {}

        json = {}

        if isinstance(data, Mapping):
            data = [data]

        for document in data:
            for key in document:
                if document[key].__class__.__name__ == "ObjectId":
                    json[key] = str(document[key])
                else:
                    json[key] = document[key]

        return json
