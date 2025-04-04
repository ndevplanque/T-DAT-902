import psycopg2
from unittest.mock import patch, MagicMock
from v1.database.postgres import Postgres

def test_postgres_connection():
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        db = Postgres()
        mock_connect.assert_called_once_with(
            dbname='gis_db',
            user='postgres',
            password='postgres',
            host='host.docker.internal',
            port='5432'
        )
        assert db.conn == mock_conn
        assert db.conn.autocommit is True
        assert db.cursor == mock_conn.cursor()

def test_postgres_close():
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        db = Postgres()
        db.close()
        db.cursor.close.assert_called_once()
        db.conn.close.assert_called_once()

def test_postgres_fetchall():
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        db = Postgres()
        query = "SELECT * FROM test_table"
        params = None
        mock_cursor.fetchall.return_value = [('row1',), ('row2',)]

        result = db.fetchall(query, params)
        mock_cursor.execute.assert_called_once_with(query, params)
        assert result == [('row1',), ('row2',)]

def test_postgres_fetchall_error():
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        db = Postgres()
        query = "SELECT * FROM test_table"
        params = None
        mock_cursor.execute.side_effect = psycopg2.Error("Erreur SQL")

        result = db.fetchall(query, params)
        mock_cursor.execute.assert_called_once_with(query, params)
        assert result == []
