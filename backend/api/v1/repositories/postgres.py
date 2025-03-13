import psycopg2

conn = None
cursor = None

def connect():
    global conn, cursor
    conn = psycopg2.connect(dbname='gis_db', user='postgres', password='postgres', host='host.docker.internal', port='5432')
    cursor = conn.cursor()
    return cursor

def close():
    global conn, cursor
    cursor.close()
    conn.close()
