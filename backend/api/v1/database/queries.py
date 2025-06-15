from v1.models.bounds import Bounds


def list_cities_map_areas(bounds: Bounds):
    return f"""
        SELECT cities.city_id as id, name, ST_AsGeoJSON(geom) as geo_json, nb_transactions, prix_min as area_min_price, prix_max as area_max_price, prix_m2_moyen as area_average_price  
        FROM cities 
        LEFT JOIN properties_cities_stats ON cities.city_id = properties_cities_stats.city_id
        WHERE ST_Intersects(geom, ST_MakeEnvelope({bounds.sw_lon}, {bounds.sw_lat}, {bounds.ne_lon}, {bounds.ne_lat}, 4326));
        """


def list_departments_map_areas(bounds: Bounds):
    return f"""
        SELECT departments.department_id as id, name, ST_AsGeoJSON(geom) as geo_json, nb_transactions_total as nb_transactions, prix_min as area_min_price, prix_max as area_max_price, prix_m2_moyen as area_average_price
        FROM departments 
        LEFT JOIN properties_departments_stats ON departments.department_id = properties_departments_stats.department_id
        WHERE ST_Intersects(geom, ST_MakeEnvelope({bounds.sw_lon}, {bounds.sw_lat}, {bounds.ne_lon}, {bounds.ne_lat}, 4326));
        """


def list_regions_map_areas(bounds: Bounds):
    return f"""
        SELECT regions.region_id as id, name, ST_AsGeoJSON(geom) as geo_json, nb_transactions_total as nb_transactions, prix_min as area_min_price, prix_max as area_max_price, prix_m2_moyen as area_average_price
        FROM regions 
        LEFT JOIN properties_regions_stats ON regions.region_id = properties_regions_stats.region_id
        WHERE ST_Intersects(geom, ST_MakeEnvelope({bounds.sw_lon}, {bounds.sw_lat}, {bounds.ne_lon}, {bounds.ne_lat}, 4326));
        """


def list_cities():
    return f"""
        SELECT cities.city_id as id, name, nb_transactions, prix_min as area_min_price, prix_max as area_max_price, prix_m2_moyen as area_average_price  
        FROM cities 
        LEFT JOIN properties_cities_stats ON cities.city_id = properties_cities_stats.city_id;
        """


def list_departments():
    return f"""
           SELECT departments.department_id as id, name, nb_transactions_total as nb_transactions, prix_min as area_min_price, prix_max as area_max_price, prix_m2_moyen as area_average_price
           FROM departments 
           LEFT JOIN properties_departments_stats ON departments.department_id = properties_departments_stats.department_id;
           """


def list_regions():
    return f"""
           SELECT regions.region_id as id, name, nb_transactions_total as nb_transactions, prix_min as area_min_price, prix_max as area_max_price, prix_m2_moyen as area_average_price
           FROM regions 
           LEFT JOIN properties_regions_stats ON regions.region_id = properties_regions_stats.region_id
           """


def list_cities_properties(cities_ids):
    formatted_ids = ", ".join(f"'{str(id)}'" for id in cities_ids)
    return f"""
        SELECT date_mutation, valeur_fonciere, surface_reelle_bati, surface_terrain
        FROM properties
        WHERE code_commune IN ({formatted_ids})
        """
