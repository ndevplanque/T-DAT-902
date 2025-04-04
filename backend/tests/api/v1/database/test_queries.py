from test_helper import mocked_map_areas_bounds
from v1.database.queries import (
    list_cities_map_areas,
    list_departments_map_areas,
    list_regions_map_areas,
    list_cities_prices,
    list_departments_prices,
    list_regions_prices,
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


def test_list_cities_prices():
    query = list_cities_prices()
    assert "SELECT city_id, name FROM cities;" in query


def test_list_departments_prices():
    query = list_departments_prices()
    assert "SELECT department_id, name FROM departments;" in query


def test_list_regions_prices():
    query = list_regions_prices()
    assert "SELECT region_id, name FROM regions;" in query
