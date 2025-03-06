import pytest
from unittest import mock
from api.v1.services.map import map

def test_map(mocker):
    """Test la fonction map qui importe les données et les passes à au layer_adapter"""
    get_cities = mocker.patch("api.v1.services.map.repository.get_cities", return_value={"zones": [{"nom": "une_zone"}]})
    get_departments = mocker.patch("api.v1.services.map.repository.get_departments", return_value={"zones": [{"nom": "une_zone"}]})
    get_regions = mocker.patch("api.v1.services.map.repository.get_regions", return_value={"zones": [{"nom": "une_zone"}]})

    result = map()

    get_cities.assert_called_once()
    get_departments.assert_called_once()
    get_regions.assert_called_once()

    # Vérifier la structure de la réponse
    assert isinstance(result, dict)
    assert "layers" in result
    assert isinstance(result["layers"], dict)
    assert set(result["layers"].keys()) == {"cities", "departments", "regions"}  # Vérifie les clés exactes
    assert all(isinstance(layer, dict) and "zones" in layer for layer in result["layers"].values())

def test_map_empty_zones(mocker):
    """Test que map lève une ValueError si zones est vide"""
    mocker.patch("api.v1.services.map.repository.get_cities", return_value={"zones": []})
    mocker.patch("api.v1.services.map.repository.get_departments", return_value={"zones": []})
    mocker.patch("api.v1.services.map.repository.get_regions", return_value={"zones": []})

    with pytest.raises(ValueError, match="est vide"):
        map()
