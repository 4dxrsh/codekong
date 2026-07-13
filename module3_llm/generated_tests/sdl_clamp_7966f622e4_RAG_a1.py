from demo_range_utils import clamp

def test_clamp_upper_bound():
    assert clamp(15, 0, 10) == 10, "Should return hi when x > hi"