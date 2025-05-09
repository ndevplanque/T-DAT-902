import psycopg2, logs

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
        """Exécute une requête SQL et retourne tous les résultats"""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            logs.info(f"Erreur SQL : {e}")  # Log l'erreur au lieu de planter
            return []

    def fetchone(self, query, params=None):
        """Exécute une requête SQL et retourne un seul résultat"""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        except psycopg2.Error as e:
            logs.info(f"Erreur SQL : {e}")  # Log l'erreur au lieu de planter
            return []

    def schema(self):
        """Retourne le schéma de la base de données"""
        cities_example_row = self.fetchone("SELECT * from cities ORDER BY city_id LIMIT 1")
        cities_columns = [desc[0] for desc in self.cursor.description]
        cities_example = {}
        for i in range(0, len(cities_columns)-1):
            cities_example[cities_columns[i]] = cities_example_row[i]

        departments_example_row = self.fetchone("SELECT * from departments ORDER BY department_id LIMIT 1")
        departments_columns = [desc[0] for desc in self.cursor.description]
        departments_example = {}
        for i in range(0, len(departments_columns)-1):
            departments_example[departments_columns[i]] = departments_example_row[i]

        regions_example_row = self.fetchone("SELECT * from regions ORDER BY region_id LIMIT 1")
        regions_columns = [desc[0] for desc in self.cursor.description]
        regions_example = {}
        for i in range(0, len(regions_columns)-1):
            regions_example[regions_columns[i]] = regions_example_row[i]

        return {
            "db_name": "gis_db",
            "ok": True,
            "tables_count": 3,
            "tables": {
                "cities": {
                    "example": cities_example,
                    "columns": cities_columns,
                },
                "departments": {
                    "example": departments_example,
                    "columns": departments_columns,
                },
                "regions": {
                    "example": regions_example,
                    "columns": regions_columns,
                },
            }
        }