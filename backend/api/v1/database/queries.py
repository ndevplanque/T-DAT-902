def list_cities():
    return "SELECT city_id, name, ST_AsText(geom) FROM cities;"

def list_departments():
    return "SELECT department_id, name, ST_AsText(geom) FROM departments;"

def list_regions():
    return "SELECT region_id, name, ST_AsText(geom) FROM regions;"

def list_cities_prices():
    return "SELECT city_id, name FROM cities;"

def list_departments_prices():
    return "SELECT department_id, name FROM departments;"

def list_regions_prices():
    return "SELECT region_id, name FROM regions;"
