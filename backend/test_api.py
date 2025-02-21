import pytest
from api import app

@pytest.fixture
def client():
    app.config["TESTING"] = True  # Active le mode test
    with app.test_client() as client:
        yield client

def test_api_v1_health(client):
    """Test de l'endpoint /api/v1/health"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json == {"success": True}

def test_api_v1_data(client):
    """Test de l'endpoint /api/v1/data"""
    response = client.get("/api/v1/data")
    assert response.status_code == 200
    assert response.json == {"message": "Hello from Flask!", "value": 42}
