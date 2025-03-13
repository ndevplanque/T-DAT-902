import psycopg2

class Postgres:
    conn = None
    cursor = None

    def __init__(self):
        self.conn = psycopg2.connect(dbname='gis_db', user='postgres', password='postgres', host='host.docker.internal', port='5432')
        self.cursor = self.conn.cursor()

    def close(self):
        self.cursor.close()
        self.conn.close()

    def execute(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchall()
