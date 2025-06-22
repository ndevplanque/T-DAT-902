import v1.features.map_transactions.repository as repository
import time, logs


def map_transactions(bounds):
    """Récupère les transactions à afficher sur la carte."""

    if bounds is None:
        raise ValueError("Bounds cannot be None")

    start = time.perf_counter()

    fc = repository.get_transactions(bounds)

    end = time.perf_counter()

    execution_time_sec = f"{end - start:.2f}"

    logs.info(f"Map transactions retrieved in {execution_time_sec} seconds.")

    return fc
