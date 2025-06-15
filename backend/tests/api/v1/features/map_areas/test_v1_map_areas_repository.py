import json
from unittest.mock import patch, MagicMock
from test_helper import mocked_map_areas_feature_collection, mocked_map_areas_bounds
from v1.features.map_areas.repository import (
    get_feature_collection,
    get_cities_feature_collection,
    get_departments_feature_collection,
    get_regions_feature_collection,
    extract_entity,
    parse_query_result,
)


@patch('v1.features.map_areas.repository.get_cities_feature_collection')
@patch('v1.features.map_areas.repository.get_departments_feature_collection')
@patch('v1.features.map_areas.repository.get_regions_feature_collection')
def test_get_feature_collection(
        mock_get_regions_feature_collection,
        mock_get_departments_feature_collection,
        mock_get_cities_feature_collection,
):
    """Test de la fonction get_feature_collection"""
    mock_get_cities_feature_collection.return_value = mocked_map_areas_feature_collection()
    mock_get_departments_feature_collection.return_value = mocked_map_areas_feature_collection()
    mock_get_regions_feature_collection.return_value = mocked_map_areas_feature_collection()

    bounds = mocked_map_areas_bounds()

    # Test pour les villes
    result = get_feature_collection("cities", bounds)

    mock_get_cities_feature_collection.assert_called_once_with(bounds)
    mock_get_departments_feature_collection.assert_not_called()
    mock_get_regions_feature_collection.assert_not_called()

    assert result == mock_get_cities_feature_collection.return_value

    # Test pour les départements
    result = get_feature_collection("departments", bounds)

    mock_get_departments_feature_collection.assert_called_once_with(bounds)
    mock_get_regions_feature_collection.assert_not_called()

    assert result == mock_get_departments_feature_collection.return_value

    # Test pour les régions
    result = get_feature_collection("regions", bounds)

    mock_get_regions_feature_collection.assert_called_once_with(bounds)

    assert result == mock_get_regions_feature_collection.return_value

    # Test pour une entité invalide
    try:
        get_feature_collection("invalid_entity", bounds)
        assert False, "Expected an exception for invalid entity"
    except ValueError as e:
        assert str(e) == "Invalid entity"


@patch('v1.features.map_areas.repository.parse_query_result')
@patch('v1.database.queries.list_cities_map_areas')
def test_get_cities_feature_collection(mock_list_cities, mock_parse_query_result):
    """Test de la fonction get_cities_feature_collection"""
    bounds = mocked_map_areas_bounds()

    features = [{}]
    min_price = 1500
    max_price = 6000

    # Mock de la fonction list_cities et parse_query_result
    mock_list_cities.return_value = "SELECT * FROM cities"
    mock_parse_query_result.return_value = features, min_price, max_price

    result = get_cities_feature_collection(bounds)

    mock_list_cities.assert_called_once_with(bounds)
    mock_parse_query_result.assert_called_once_with(mock_list_cities.return_value)

    assert result == {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "name": "Villes",
            "min_price": min_price,
            "max_price": max_price,
            "show": True
        }
    }


@patch('v1.features.map_areas.repository.parse_query_result')
@patch('v1.database.queries.list_departments_map_areas')
def test_get_departments_feature_collection(mock_list_departments, mock_parse_query_result):
    """Test de la fonction get_departments_feature_collection"""
    bounds = mocked_map_areas_bounds()

    features = [{}]
    min_price = 1500
    max_price = 6000

    # Mock de la fonction list_departments et parse_query_result
    mock_list_departments.return_value = "SELECT * FROM departments"
    mock_parse_query_result.return_value = features, min_price, max_price

    result = get_departments_feature_collection(bounds)

    mock_list_departments.assert_called_once_with(bounds)
    mock_parse_query_result.assert_called_once_with(mock_list_departments.return_value)

    assert result == {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "name": "Départements",
            "min_price": min_price,
            "max_price": max_price,
            "show": True
        }
    }


@patch('v1.features.map_areas.repository.parse_query_result')
@patch('v1.database.queries.list_regions_map_areas')
def test_get_regions_feature_collection(mock_list_regions, mock_parse_query_result):
    """Test de la fonction get_regions_feature_collection"""
    bounds = mocked_map_areas_bounds()

    features = [{}]
    min_price = 1500
    max_price = 6000

    # Mock de la fonction list_regions et parse_query_result
    mock_list_regions.return_value = "SELECT * FROM regions"
    mock_parse_query_result.return_value = features, min_price, max_price

    result = get_regions_feature_collection(bounds)

    mock_list_regions.assert_called_once_with(bounds)
    mock_parse_query_result.assert_called_once_with(mock_list_regions.return_value)

    assert result == {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "name": "Régions",
            "min_price": min_price,
            "max_price": max_price,
            "show": True
        }
    }


def test_get_feature_collection_invalid_entity():
    """Test de la fonction get_feature_collection avec une entité invalide"""
    bounds = mocked_map_areas_bounds()

    try:
        get_feature_collection("invalid_entity", bounds)
        assert False, "Expected an exception for invalid entity"
    except ValueError as e:
        assert str(e) == "Invalid entity"


@patch('v1.features.map_areas.repository.get_departments_feature_collection')
@patch('v1.features.map_areas.repository.get_cities_feature_collection')
def test_get_feature_collection_with_more_than_500_cities(
        mock_get_cities_feature_collection,
        mock_get_departments_feature_collection
):
    """Test de la fonction get_feature_collection"""
    bounds = mocked_map_areas_bounds()

    mock_get_cities_feature_collection.return_value = mocked_map_areas_feature_collection(500)
    mock_get_departments_feature_collection.return_value = mocked_map_areas_feature_collection()

    result = get_feature_collection("cities", bounds)

    # Comme il y a plus de 500 villes, on doit renvoyer les départements
    mock_get_cities_feature_collection.assert_called_once_with(bounds)
    mock_get_departments_feature_collection.assert_called_once_with(bounds)

    assert result == mock_get_departments_feature_collection.return_value


@patch('v1.features.map_areas.repository.get_regions_feature_collection')
@patch('v1.features.map_areas.repository.get_departments_feature_collection')
def test_get_feature_collection_with_more_than_500_departments(
        mock_get_departments_feature_collection,
        mock_get_regions_feature_collection,
):
    """Test de la fonction get_feature_collection"""
    bounds = mocked_map_areas_bounds()

    mock_get_departments_feature_collection.return_value = mocked_map_areas_feature_collection(500)
    mock_get_regions_feature_collection.return_value = mocked_map_areas_feature_collection()

    result = get_feature_collection("departments", bounds)

    # Comme il y a plus de 500 villes, on doit renvoyer les départements
    mock_get_departments_feature_collection.assert_called_once_with(bounds)
    mock_get_regions_feature_collection.assert_called_once_with(bounds)

    assert result == mock_get_regions_feature_collection.return_value


def test_extract_entity():
    """Test de la fonction extract_entity"""
    assert extract_entity("SELECT * FROM cities") == "cities"
    assert extract_entity("SELECT * FROM departments") == "departments"
    assert extract_entity("SELECT * FROM regions") == "regions"
    assert extract_entity("SELECT * FROM unknown_table") is None
    assert extract_entity("") is None


@patch('v1.features.map_areas.repository.Postgres')
def test_parse_query_result(mock_postgres):
    """Test de la fonction parse_query_result avec mock de la base de données et fetchall"""

    id1 = 1
    name1 = 'City1'
    geo_json1 = json.dumps({"type": "Point", "coordinates": [2.3522, 48.8566]})
    nb_transactions1 = 50
    area_min_price1 = 100
    area_max_price1 = 5000
    area_average_price1 = 2000

    id2 = 2
    name2 = 'City2'
    geo_json2 = json.dumps({"type": "Point", "coordinates": [2.3523, 48.8567]})
    nb_transactions2 = 100
    area_min_price2 = 500
    area_max_price2 = 10000
    area_average_price2 = 3000

    # Mock de la méthode fetchall
    mock_db_instance = MagicMock()
    mock_db_instance.fetchall.return_value = [
        (id1, name1, geo_json1, nb_transactions1, area_min_price1, area_max_price1, area_average_price1),
        (id2, name2, geo_json2, nb_transactions2, area_min_price2, area_max_price2, area_average_price2),
    ]
    mock_postgres.return_value = mock_db_instance

    features, min_price, max_price = parse_query_result("SELECT * FROM cities")

    assert isinstance(features, list)
    assert min_price is area_average_price1
    assert max_price is area_average_price2
    assert features == [{
        "type": "Feature",
        "properties": {
            "id": id1,
            "name": name1,
            "price": area_average_price1,
            "max_price": area_max_price1,
            "min_price": area_min_price1,
            "word_cloud_url": f"api/v1/word-clouds/cities/{id1}",
            "sentiments_url": f"api/v1/sentiments/cities/{id1}",
        },
        "geometry": json.loads(geo_json1)
    }, {
        "type": "Feature",
        "properties": {
            "id": id2,
            "name": name2,
            "price": area_average_price2,
            "max_price": area_max_price2,
            "min_price": area_min_price2,
            "word_cloud_url": f"api/v1/word-clouds/cities/{id2}",
            "sentiments_url": f"api/v1/sentiments/cities/{id2}",
        },
        "geometry": json.loads(geo_json2)
    }]
