import pytest
from unittest import mock
import json
import numpy as np
from api.v1.services.map import map, load_geojson, generate_random_price, layer_from_geojson, layer_builder

@pytest.fixture
def mock_geojson():
    """Mock d'un fichier GeoJSON avec deux zones"""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"nom": "Zone A"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-0.5, 51.5], [-0.4, 51.5], [-0.4, 51.6], [-0.5, 51.6], [-0.5, 51.5]]]
                }
            },
            {
                "type": "Feature",
                "properties": {"nom": "Zone B"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-0.3, 51.4], [-0.2, 51.4], [-0.2, 51.5], [-0.3, 51.5], [-0.3, 51.4]]]
                }
            }
        ]
    }

def test_generate_random_price():
    """Test que les prix générés sont bien dans la plage définie"""
    for _ in range(100):
        price = generate_random_price()
        assert 1500 <= price <= 6000  # Vérifie que le prix est bien dans la fourchette donnée

def test_layer_builder():
    """Test que layer_builder construit bien une structure correcte"""
    mock_zones = [
        {"name": "Zone A", "coordinates": [[1, 2], [3, 4]], "price": 2500},
        {"name": "Zone B", "coordinates": [[5, 6], [7, 8]], "price": 3200}
    ]
    result = layer_builder("Test Layer", mock_zones, 2500, 3200)

    assert isinstance(result, dict)
    assert result["name"] == "Test Layer"
    assert result["zones"] == mock_zones
    assert result["min_price"] == 2500
    assert result["max_price"] == 3200

def test_layer_from_geojson(mock_geojson, mocker):
    """Test que layer_from_geojson construit bien les données de zones"""
    mocker.patch("api.v1.services.map.generate_random_price", side_effect=[2000.0, 3000.0])

    result = layer_from_geojson("Communes", mock_geojson)

    assert isinstance(result, dict)
    assert result["name"] == "Communes"
    assert len(result["zones"]) == 2  # On s'attend à 2 zones
    assert result["min_price"] == 2000.0
    assert result["max_price"] == 3000.0

    # Vérification des zones
    zone_a = result["zones"][0]
    assert zone_a["name"] == "Zone A"
    assert isinstance(zone_a["coordinates"], list)
    assert len(zone_a["coordinates"]) == 5  # 5 coordonnées pour la zone A
    assert zone_a["price"] == 2000.0

    zone_b = result["zones"][1]
    assert zone_b["name"] == "Zone B"
    assert isinstance(zone_b["coordinates"], list)
    assert len(zone_b["coordinates"]) == 5  # 5 coordonnées pour la zone B
    assert zone_b["price"] == 3000.0

def test_map(mock_geojson, mocker):
    """Test la fonction map qui importe les données et les passes à au layer_adapter"""
    mocker.patch("api.v1.services.map.load_geojson", return_value=mock_geojson)
    mocker.patch("api.v1.services.map.layer_from_geojson", return_value={"some": "data"})

    result = map()

    assert isinstance(result, dict)
    assert "layers" in result
    assert len(result["layers"]) == 3  # Communes, Départements, Régions
    assert all(isinstance(layer, dict) for layer in result["layers"])
