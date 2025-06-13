import v1.features.area_listing.repository as repository


def area_listing():
    regions = repository.get_regions()
    if "items" in regions and isinstance(regions["items"], list) and not regions["items"]:
        raise ValueError("Erreur : La liste 'regions' est vide.")

    departments = repository.get_departments()
    if "items" in departments and isinstance(departments["items"], list) and not departments["items"]:
        raise ValueError("Erreur : La liste 'departments' est vide.")

    cities = repository.get_cities()
    if "items" in cities and isinstance(cities["items"], list) and not cities["items"]:
        raise ValueError("Erreur : La liste 'cities' est vide.")

    return {
        "regions": regions,
        "departments": departments,
        "cities": cities,
    }
