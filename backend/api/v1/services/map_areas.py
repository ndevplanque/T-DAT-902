import api.v1.repositories.map_areas as repository
import logging
import time

def map_areas(bounds):
    """Récupère les données des différentes couches de la carte."""

    start = time.perf_counter()

    selection = None

    if bounds is None:
        selection = "regions"
    else :
        if bounds.zoom <= 6:
            selection = "regions"
        elif bounds.zoom <= 9:
            selection = "departments"
        else:
            selection = "cities"

    fc = repository.get_feature_collection(selection, bounds)

    end = time.perf_counter()

    execution_time_sec = f"{end - start:.2f}"

    logging.info(f"Map areas retrieved in {execution_time_sec} seconds.")

    return fc
