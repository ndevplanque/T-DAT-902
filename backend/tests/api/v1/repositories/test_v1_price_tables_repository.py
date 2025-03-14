import pytest
from unittest import mock
from api.v1.repositories.price_tables import generate_random_price, response_builder

def test_generate_random_price():
    """Test que les prix générés sont bien dans la plage définie"""
    for _ in range(100):
        price = generate_random_price()
        assert 1500 <= price <= 6000  # Vérifie que le prix est bien dans la fourchette donnée

def test_response_builder():
    """Test que response_builder construit bien une structure correcte"""
    mock_items = [
        {"name": "Zone A", "price": 2500},
        {"name": "Zone B", "price": 3200}
    ]
    aggs = {
        "min_price": 2500,
        "max_price": 3200,
    }
    result = response_builder("Test Title", mock_items, aggs)

    assert isinstance(result, dict)
    assert result["title"] == "Test Title"
    assert result["items"] == mock_items
    assert result["aggs"] == aggs
