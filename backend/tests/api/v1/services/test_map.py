import pytest
from unittest import mock
import json
from api.v1.services.map import map

# Test pour la fonction map
def test_map(mocker):
    # Mock de la fonction load_geojson() pour éviter de lire un vrai fichier
    mock_geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"nom": "Zone A"},
                "geometry": {"type": "Polygon", "coordinates": [[[-0.5, 51.5], [-0.4, 51.5], [-0.4, 51.6], [-0.5, 51.6], [-0.5, 51.5]]] }
            },
            {
                "type": "Feature",
                "properties": {"nom": "Zone B"},
                "geometry": {"type": "Polygon", "coordinates": [[[-0.3, 51.4], [-0.2, 51.4], [-0.2, 51.5], [-0.3, 51.5], [-0.3, 51.4]]] }
            }
        ]
    }
    mocker.patch('api.v1.services.map.load_geojson', return_value=mock_geojson_data)

    # Mock de la fonction generate_random_price() pour éviter de dépendre de la génération aléatoire
    mocker.patch('api.v1.services.map.generate_random_price', side_effect=[2000.0, 3000.0])

    # Appel de la fonction map
    result = map()

    # Assertions pour vérifier que la structure est correcte
    assert isinstance(result, dict)
    assert 'zones' in result
    assert 'min_price' in result
    assert 'max_price' in result
    assert len(result['zones']) == 2  # On a deux zones dans le mock
    assert result['min_price'] == 2000.0
    assert result['max_price'] == 3000.0

    # Vérifier les données dans les zones
    zone_a = result['zones'][0]
    assert zone_a['name'] == 'Zone A'
    assert isinstance(zone_a['coordinates'], list)
    assert len(zone_a['coordinates']) == 5  # 5 coordonnées pour la zone A
    assert zone_a['price'] == 2000.0

    zone_b = result['zones'][1]
    assert zone_b['name'] == 'Zone B'
    assert isinstance(zone_b['coordinates'], list)
    assert len(zone_b['coordinates']) == 5  # 5 coordonnées pour la zone B
    assert zone_b['price'] == 3000.0
