from v1.models.bounds import Bounds


def test_bounds_initialization():
    bounds = Bounds(zoom=10, sw_lat=34.052235, sw_lon=-118.243683, ne_lat=40.712776, ne_lon=-74.005974)
    assert bounds.zoom == 10
    assert bounds.sw_lat == 34.052235
    assert bounds.sw_lon == -118.243683
    assert bounds.ne_lat == 40.712776
    assert bounds.ne_lon == -74.005974


def test_bounds_default_values():
    bounds = Bounds(zoom=0, sw_lat=0.0, sw_lon=0.0, ne_lat=0.0, ne_lon=0.0)
    assert bounds.zoom == 0
    assert bounds.sw_lat == 0.0
    assert bounds.sw_lon == 0.0
    assert bounds.ne_lat == 0.0
    assert bounds.ne_lon == 0.0
