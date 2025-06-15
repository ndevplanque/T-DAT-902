from test_helper import mocked_map_areas_bounds
from v1.database.queries import (
    list_cities_map_areas,
    list_departments_map_areas,
    list_regions_map_areas,
    list_cities,
    list_departments,
    list_regions,
    list_cities_properties,
)


def test_list_cities_map_areas():
    bounds = mocked_map_areas_bounds()
    query = list_cities_map_areas(bounds)
    assert "ST_Intersects" in query
    assert "ST_MakeEnvelope" in query


def test_list_departments_map_areas():
    bounds = mocked_map_areas_bounds()
    query = list_departments_map_areas(bounds)
    assert "ST_Intersects" in query
    assert "ST_MakeEnvelope" in query


def test_list_regions_map_areas():
    bounds = mocked_map_areas_bounds()
    query = list_regions_map_areas(bounds)
    assert "ST_Intersects" in query
    assert "ST_MakeEnvelope" in query


def test_list_cities():
    query = list_cities()
    assert "SELECT cities.city_id as id, name" in query
    assert "FROM cities" in query
    assert "LEFT JOIN properties_cities_stats" in query


def test_list_departments():
    query = list_departments()
    assert "SELECT departments.department_id as id, name" in query
    assert "FROM departments" in query
    assert "LEFT JOIN properties_departments_stats" in query


def test_list_regions():
    query = list_regions()
    assert "SELECT regions.region_id as id, name" in query
    assert "FROM regions" in query
    assert "LEFT JOIN properties_regions_stats" in query


def test_list_cities_properties():
    cities_ids = [123, 456]
    query = list_cities_properties(cities_ids)
    assert "SELECT date_mutation, valeur_fonciere" in query
    assert "FROM properties" in query
    assert "WHERE code_commune IN ('123', '456')" in query
