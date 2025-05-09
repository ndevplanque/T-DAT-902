import v1.features.area_details.repository as repository


def area_details(entity, id):
    # Vérifier que l'entité est valide
    if entity not in ["cities", "departments", "regions"]:
        raise AttributeError("Les nuages de mots ne sont disponibles que pour les 'cities', 'departments' ou 'regions'")

    return repository.get_area_details(entity, id)
