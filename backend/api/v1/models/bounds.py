from dataclasses import dataclass

@dataclass
class Bounds:
    zoom: int
    sw_lat: float
    sw_lon: float
    ne_lat: float
    ne_lon: float
