import logs
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from pymongo.cursor import Cursor
from collections.abc import Mapping
from bson import ObjectId


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

    def find(self, collection: str, query=None, fields=None):
        """Exécute une requête pour récupérer tous les documents correspondant à la requête"""
        try:
            return self.db[collection].find(query, fields)
        except PyMongoError as e:
            logs.info(f"Erreur MongoDB : {e}")
            return []

    def find_one(self, collection: str, query=None, fields=None):
        """Exécute une requête pour récupérer un document correspondant à la requête"""
        try:
            return self.db[collection].find_one(query, fields)
        except PyMongoError as e:
            logs.info(f"Erreur MongoDB : {e}")
            return None

    def fields(self, collection: str):
        """Retourne les champs de la collection"""
        try:
            return list(self.db[collection].find_one().keys())
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
                sample_item = self.find_one(collection=name)
                collections[name] = {"example": MongoDB.json(sample_item), "keys": {}}
                for key in sample_item.keys():
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
        """Convertit un document ou une liste de documents Mongo en JSON serializable"""

        def convert_document(doc):
            result = {}
            for key, value in doc.items():
                if isinstance(value, ObjectId):
                    result[key] = str(value)
                else:
                    result[key] = value
            return result

        # Si c'est un document seul
        if isinstance(data, Mapping):
            return convert_document(data)

        # Si c'est un curseur ou une liste de documents
        if isinstance(data, (list, Cursor)):
            return [convert_document(doc) for doc in data]

        # Si c'est vide ou d'un type inconnu
        return {}

    @staticmethod
    def only_fields(fields):
        """Un filtre pour spécifier les champs à retourner"""
        if not isinstance(fields, list):
            return {}
        else:
            f = {field: 1 for field in fields}
            if "_id" not in f:
                f["_id"] = 0
        return f
