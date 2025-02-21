import pytest
from unittest.mock import patch
from api import app

@pytest.fixture
def client():
    app.config["TESTING"] = True  # Active le mode test
    with app.test_client() as client:
        yield client

# Test pour l'endpoint /api/v1/health
def test_api_v1_health(client):
    with patch("v1.services.health.health") as mock_health:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        mock_health.assert_called_once()

# Test pour l'endpoint /api/v1/example
def test_api_v1_example(client):
    with patch("v1.services.example.example") as mock_example:
        response = client.get("/api/v1/example")
        assert response.status_code == 200
        mock_example.assert_called_once()
