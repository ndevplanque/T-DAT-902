import pytest
from unittest import mock
from api.v1.services.price_tables import price_tables

cities_prices = "api.v1.services.price_tables.repository.get_cities_prices"
departments_prices = "api.v1.services.price_tables.repository.get_departments_prices"
regions_prices = "api.v1.services.price_tables.repository.get_regions_prices"

def test_price_tables(mocker):
    """Test la fonction price_tables qui importe les données des prix des différentes zones"""
    get_cities_prices = mocker.patch(cities_prices, return_value={"zones": [{"nom": "une_zone"}]})
    get_departments_prices = mocker.patch(departments_prices, return_value={"zones": [{"nom": "une_zone"}]})
    get_regions_prices = mocker.patch(regions_prices, return_value={"zones": [{"nom": "une_zone"}]})

    result = price_tables()

    get_cities_prices.assert_called_once()
    get_departments_prices.assert_called_once()
    get_regions_prices.assert_called_once()

    # Vérifier la structure de la réponse
    assert isinstance(result, dict)
    assert "price_tables" in result
    assert isinstance(result["price_tables"], list)

def test_price_tables_empty_items(mocker):
    """Test que price_tables lève une ValueError si items est vide"""
    mocker.patch(cities_prices, return_value={"items": []})
    mocker.patch(departments_prices, return_value={"items": []})
    mocker.patch(regions_prices, return_value={"items": []})

    with pytest.raises(ValueError, match="est vide"):
        price_tables()
