from unittest.mock import patch
from v1.features.map_areas.service import map_areas, get_entity_from_zoom
from v1.models.bounds import Bounds


@patch('v1.features.map_areas.repository.get_feature_collection')
@patch('v1.features.map_areas.service.get_entity_from_zoom')
def test_map_areas(mock_get_entity_from_zoom, mock_get_feature_collection):
    """Test de la fonction map_areas"""

    mock_get_feature_collection.return_value = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [2.3522, 48.8566]}}]
    }
    mock_get_entity_from_zoom.return_value = "cities"

    # Test avec des coordonnées valides
    bounds = Bounds(10, 48.8566, 2.3522, 48.8567, 2.3523)  # Paris
    result = map_areas(bounds)
    assert result is mock_get_feature_collection.return_value

    # Vérifie que la fonction mockée est appelée une fois
    mock_get_feature_collection.assert_called_once()
    mock_get_entity_from_zoom.assert_called_once_with(bounds)

    try:
        result_invalid = map_areas(None)
        assert False, "Expected an exception for invalid coordinates"
    except ValueError as e:
        assert str(e) == "Bounds cannot be None"


def test_get_entity_from_zoom():
    """Test de la fonction get_entity_from_zoom"""

    for zoom in range(1, 15):
        bounds = Bounds(zoom, 48.8566, 2.3522, 48.8567, 2.3523)
        entity = get_entity_from_zoom(bounds)
        if zoom <= 6:
            assert entity == "regions"
        elif zoom <= 9:
            assert entity == "departments"
        else:
            assert entity == "cities"
