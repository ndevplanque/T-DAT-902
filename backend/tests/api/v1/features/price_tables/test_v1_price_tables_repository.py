from unittest.mock import patch, MagicMock
from v1.features.price_tables.repository import (
    get_cities_prices,
    get_departments_prices,
    get_regions_prices,
    parse_query_result,
    generate_random_price,
    response_builder,
)


@patch('v1.features.price_tables.repository.parse_query_result')
@patch('v1.database.queries.list_cities_prices')
def test_get_cities_prices(mock_list_cities_prices, mock_parse_query_result):
    data = [{}] * 5
    aggs = {}

    # Mock de la fonction list_departments et parse_query_result
    mock_list_cities_prices.return_value = "SELECT * FROM cities"
    mock_parse_query_result.return_value = data, aggs

    result = get_cities_prices()
    assert result == response_builder("Villes", data, aggs)


@patch('v1.features.price_tables.repository.parse_query_result')
@patch('v1.database.queries.list_departments_prices')
def test_get_departments_prices(mock_list_departments_prices, mock_parse_query_result):
    data = [{}] * 5
    aggs = {}

    # Mock de la fonction list_departments et parse_query_result
    mock_list_departments_prices.return_value = "SELECT * FROM departments"
    mock_parse_query_result.return_value = data, aggs

    result = get_departments_prices()
    assert result == response_builder("Départements", data, aggs)


@patch('v1.features.price_tables.repository.parse_query_result')
@patch('v1.database.queries.list_regions_prices')
def test_get_regions_prices(mock_list_regions_prices, mock_parse_query_result):
    data = [{}] * 5
    aggs = {}

    # Mock de la fonction list_departments et parse_query_result
    mock_list_regions_prices.return_value = "SELECT * FROM regions"
    mock_parse_query_result.return_value = data, aggs

    result = get_regions_prices()
    assert result == response_builder("Régions", data, aggs)


@patch('v1.features.price_tables.repository.generate_random_price')
@patch('v1.features.price_tables.repository.Postgres')
def test_parse_query_result(mock_postgres, mock_generate_random_price):
    """Test de la fonction parse_query_result avec mock de la base de données et fetchall"""

    id1 = 1
    name1 = 'City1'
    price1 = 2000

    id2 = 2
    name2 = 'City2'
    price2 = 3000

    # Mock de la méthode fetchall
    mock_db_instance = MagicMock()
    mock_db_instance.fetchall.return_value = [(id1, name1), (id2, name2)]
    mock_postgres.return_value = mock_db_instance

    # Mock de la fonction generate_random_price
    mock_generate_random_price.side_effect = [price1, price2]

    data, aggs = parse_query_result("SELECT * FROM cities")

    assert data == [{
        "id": id1,
        "name": name1,
        "price": price1,
    }, {
        "id": id2,
        "name": name2,
        "price": price2,
    }]
    assert aggs == {
        "min_price": price1,
        "max_price": price2,
    }


def test_generate_random_price():
    """Test que les prix générés sont bien dans la plage définie"""
    for _ in range(100):
        assert 1500 <= generate_random_price() <= 6000


def test_response_builder():
    """Test que la fonction response_builder construit correctement la réponse"""
    title = "Test Title"
    items = [{}] * 5
    aggs = {}

    assert response_builder(title, items, aggs) == {
        "title": title,
        "items": items,
        "aggs": aggs
    }
