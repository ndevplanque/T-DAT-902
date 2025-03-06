import pytest
from unittest import mock
from api.v1.repositories.map import generate_random_price, layer_builder

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
