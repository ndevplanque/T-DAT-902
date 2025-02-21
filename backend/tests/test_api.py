import pytest
from api import app

# Test client Flask
@pytest.fixture
def client():
    app.config["TESTING"] = True  # Active le mode test
    with app.test_client() as client:
        yield client

# Test pour l'endpoint /api/v1/health
def test_api_v1_health(client, mocker):
    # Patch la fonction health utilisée dans api.py
    mock_health = mocker.patch("v1.services.health.health")
    response = client.get("/api/v1/health")

    # Assertions
    assert response.status_code == 200
    mock_health.assert_called_once()  # Vérifie que health() a été appelé une fois

# Test pour l'endpoint /api/v1/example
def test_api_v1_example(client, mocker):
    with mocker.patch("v1.services.example.example") as mock_example:
        response = client.get("/api/v1/example")
        assert response.status_code == 200
        mock_example.assert_called_once()  # Vérifie que example() a été appelé