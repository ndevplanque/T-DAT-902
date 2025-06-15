import pytest
from main import app, handle_exception


# Test client Flask
@pytest.fixture
def client():
    app.config["TESTING"] = True  # Active le mode test
    with app.test_client() as client:
        yield client


# Test de l'endpoint racine
def test_root(client):
    """Test de l'endpoint racine"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.data.decode("utf-8") == "Welcome to Homepedia API"


def test_api_v1_health(client, mocker):
    """Test de l'endpoint /api/v1/health"""
    mock_health = mocker.patch("main.v1_health", return_value={"health": "mocked"})

    response = client.get("/api/v1/health")

    mock_health.assert_called_once()

    assert response.status_code == 200
    assert response.json == mock_health.return_value


def test_api_v1_map_areas(client, mocker):
    """Test de l'endpoint /api/v1/map-areas/<zoom>/<sw_lat>/<sw_lon>/<ne_lat>/<ne_lon>"""
    mock_map_areas = mocker.patch("main.v1_map_areas", return_value={"map_areas": "mocked"})

    response = client.get("/api/v1/map-areas/10/48.8566/2.3522/48.8567/2.3523")

    mock_map_areas.assert_called_once()

    assert response.status_code == 200
    assert response.json == mock_map_areas.return_value


def test_api_v1_sentiments(client, mocker):
    """Test de l'endpoint /api/v1/sentiments/<entity>/<id>"""
    mock_sentiments = mocker.patch("main.v1_sentiments", return_value={"sentiments": "mocked"})

    response = client.get("/api/v1/sentiments/cities/123")

    mock_sentiments.assert_called_once()

    assert response.status_code == 200
    assert response.json == mock_sentiments.return_value


def test_api_v1_word_clouds(client, mocker):
    """Test de l'endpoint /api/v1/word-clouds/<entity>/<id>"""
    mock_word_clouds = mocker.patch("main.v1_word_clouds", return_value={"word_clouds": "mocked"})

    response = client.get("/api/v1/word-clouds/cities/123")

    mock_word_clouds.assert_called_once()

    assert response.status_code == 200
    assert response.json == mock_word_clouds.return_value


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
