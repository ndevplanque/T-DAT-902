import pytest
from api.main import app

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
    # Patch la fonction map et retourne une valeur compatible JSON
    mock_map = mocker.patch("api.main.v1_map", return_value={"some": "data"})
    response = client.get("/api/v1/map")

    assert response.status_code == 200
    mock_map.assert_called_once()  # Vérifie que map() a été appelé