from unittest.mock import patch
from v1.features.price_tables.service import price_tables


@patch('v1.features.price_tables.repository.get_cities_prices')
@patch('v1.features.price_tables.repository.get_departments_prices')
@patch('v1.features.price_tables.repository.get_regions_prices')
def test_price_tables(
        mock_get_regions_prices,
        mock_get_departments_prices,
        mock_get_cities_prices,
):
    """Test de la fonction price_tables"""
    mock_get_regions_prices.return_value = {"data": "regions"}
    mock_get_departments_prices.return_value = {"data": "departments"}
    mock_get_cities_prices.return_value = {"data": "cities"}

    result = price_tables()

    assert result == {
        "price_tables": [
            mock_get_regions_prices.return_value,
            mock_get_departments_prices.return_value,
            mock_get_cities_prices.return_value,
        ]
    }
