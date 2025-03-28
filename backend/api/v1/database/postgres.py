import psycopg2

class Postgres:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname='gis_db',
            user='postgres',
            password='postgres',
            host='host.docker.internal',
            port='5432'
        )
        self.conn.autocommit = True  # Active le mode autocommit pour éviter les blocages
        self.cursor = self.conn.cursor()

    def __enter__(self):
        """Permet d'utiliser `with Postgres() as db`"""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Ferme proprement la connexion en fin d'utilisation"""
        self.close()

    def close(self):
        """Ferme le curseur et la connexion"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def fetchall(self, query, params=None):
        """Exécute une requête SQL en toute sécurité"""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            print(f"Erreur SQL : {e}")  # Log l'erreur au lieu de planter
            return []
