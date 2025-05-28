import v1.features.area_details.repository as repository


def area_details(entity, id):
    # Vérifier que l'entité est valide
    if entity not in ["cities"]:  # , "departments", "regions"]:
        raise AttributeError("Les détails sont disponibles que pour les 'cities'")  # , 'departments' ou 'regions'")

    return repository.get_cities_area_details(id)
