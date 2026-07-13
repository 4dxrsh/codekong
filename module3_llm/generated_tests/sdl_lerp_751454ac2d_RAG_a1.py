from demo_range_utils import lerp

def test_clamp_effect():
    assert lerp(0, 10, -0.5) == 0.0, "Should clamp t to 0.0"
    assert lerp(0, 10, 1.5) == 10.0, "Should clamp t to 1.0"