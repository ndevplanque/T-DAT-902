import v1.features.map_areas.repository as repository
import logging
import time

from v1.models.bounds import Bounds


def map_areas(bounds):
    """Récupère les données des différentes couches de la carte."""

    if bounds is None:
        raise ValueError("Bounds cannot be None")

    start = time.perf_counter()

    entity = get_entity_from_zoom(bounds)

    fc = repository.get_feature_collection(entity, bounds)

    end = time.perf_counter()

    execution_time_sec = f"{end - start:.2f}"

    logging.info(f"Map areas retrieved in {execution_time_sec} seconds.")

    return fc


def get_entity_from_zoom(bounds: Bounds):
    if bounds.zoom <= 6:
        return "regions"
    elif bounds.zoom <= 9:
        return "departments"
    else:
        return "cities"
