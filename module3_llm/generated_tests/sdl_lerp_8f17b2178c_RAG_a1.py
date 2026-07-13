from demo_range_utils import lerp

def test_lerp():
    assert lerp(0, 10, 0.5) == 5.0, "lerp should return 5.0 for inputs (0, 10, 0.5)"