import pytest
from flask import Response
from api.main import app, handle_exception

# Test client Flask
@pytest.fixture
def client():
    app.config["TESTING"] = True  # Active le mode test
    with app.test_client() as client:
        yield client

# Test pour l'endpoint /api/v1/health
def test_api_v1_health(client, mocker):
    # Patch la fonction health et retourne une valeur compatible JSON
    mock_health = mocker.patch("api.main.v1_health", return_value={"some": "data"})
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    mock_health.assert_called_once()  # Vérifie que health() a été appelé

# Test pour l'endpoint /api/v1/example
def test_api_v1_example(client, mocker):
    # Patch la fonction example et retourne une valeur compatible JSON
    mock_example = mocker.patch("api.main.v1_example", return_value={"some": "data"})
    response = client.get("/api/v1/example")

    assert response.status_code == 200
    mock_example.assert_called_once()  # Vérifie que example() a été appelé

# Test pour l'endpoint /api/v1/map
def test_api_v1_map(client, mocker):
    mock_response = Response("<html><body>Map</body></html>", status=200, content_type="text/html")
    mock_map = mocker.patch("api.main.v1_map_html", return_value=mock_response)

    response = client.get("/api/v1/map")

    # Vérifications
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/html"
    assert b"<html>" in response.data  # Vérifie que le contenu est bien du HTML
    mock_map.assert_called_once()  # Vérifie que send_html() a bien été appelé


# Test pour l'endpoint /api/v1/price-tables
def test_api_v1_price_tables(client, mocker):
    # Patch la fonction price_tables et retourne une valeur compatible JSON
    mock_price_tables = mocker.patch("api.main.v1_price_tables", return_value={"some": "data"})
    response = client.get("/api/v1/price-tables")

    assert response.status_code == 200
    mock_price_tables.assert_called_once()  # Vérifie que map() a été appelé

def test_handle_exception_with_http_error(client):
    with app.test_request_context():
        response = handle_exception(Exception("404 Not Found: Resource not found"))

        json = response[0].json
        assert json == {"error": "Not Found", "code": 404}

        status_code = response[1]
        assert status_code == 404

def test_handle_exception_with_custom_error(client):
    with app.test_request_context():
        response = handle_exception(RuntimeError("A custom error occurred"))

        json = response[0].json
        assert json == {"error": "A custom error occurred", "code": 500}

        status_code = response[1]
        assert status_code == 500
