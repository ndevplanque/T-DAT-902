import logs
from pymongo import MongoClient
from pymongo.errors import PyMongoError


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

    def find(self, collection_name, query=None, fields=None):
        """Exécute une requête pour récupérer tous les documents correspondant à la requête"""
        if query is None:
            query = {}
        if fields is None:
            fields = {}
        try:
            collection = self.db[collection_name]
            return list(collection.find(query, fields))
        except PyMongoError as e:
            logs.info(f"Erreur MongoDB : {e}")
            return []

    def insert_one(self, collection_name, document):
        """Insère un document dans la collection spécifiée"""
        try:
            collection = self.db[collection_name]
            result = collection.insert_one(document)
            return result.inserted_id
        except PyMongoError as e:
            logs.info(f"Erreur MongoDB : {e}")
            return None

    def fields(self, collection_name):
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
                collections[name] = {"keys": {}}
                sample_item = self.db[name].find_one()
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
