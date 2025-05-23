from v1.models.bounds import Bounds


def list_cities_map_areas(bounds: Bounds):
    return f"""
        SELECT city_id as id, name, ST_AsGeoJSON(geom) as geo_json
        FROM cities
        WHERE ST_Intersects(geom, ST_MakeEnvelope({bounds.sw_lon}, {bounds.sw_lat}, {bounds.ne_lon}, {bounds.ne_lat}, 4326));
        """


def list_departments_map_areas(bounds: Bounds):
    return f"""
        SELECT department_id as id, name, ST_AsGeoJSON(geom) as geo_json
        FROM departments
        WHERE ST_Intersects(geom, ST_MakeEnvelope({bounds.sw_lon}, {bounds.sw_lat}, {bounds.ne_lon}, {bounds.ne_lat}, 4326));
        """


def list_regions_map_areas(bounds: Bounds):
    return f"""
        SELECT region_id as id, name, ST_AsGeoJSON(geom) as geo_json
        FROM regions
        WHERE ST_Intersects(geom, ST_MakeEnvelope({bounds.sw_lon}, {bounds.sw_lat}, {bounds.ne_lon}, {bounds.ne_lat}, 4326));
        """


def list_cities_prices():
    return "SELECT city_id, name FROM cities;"


def list_departments_prices():
    return "SELECT department_id, name FROM departments;"


def list_regions_prices():
    return "SELECT region_id, name FROM regions;"
