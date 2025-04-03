import v1.features.price_tables.repository as repository


def price_tables():
    regions = repository.get_regions_prices()
    if "items" in regions and isinstance(regions["items"], list) and not regions["items"]:
        raise ValueError("Erreur : La liste 'regions' est vide.")

    departments = repository.get_departments_prices()
    if "items" in departments and isinstance(departments["items"], list) and not departments["items"]:
        raise ValueError("Erreur : La liste 'departments' est vide.")

    cities = repository.get_cities_prices()
    if "items" in cities and isinstance(cities["items"], list) and not cities["items"]:
        raise ValueError("Erreur : La liste 'cities' est vide.")

    return {
        "price_tables": [regions, departments, cities]
    }
