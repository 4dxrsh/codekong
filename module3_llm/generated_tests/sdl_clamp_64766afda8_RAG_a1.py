from demo_range_utils import clamp

def test_clamp_with_low_value():
    assert clamp(-1, 0, 10) == 0, "Should return lo when x is less than lo"

def test_clamp_with_high_value():
    assert clamp(15, 0, 10) == 10, "Should return hi when x is greater than hi"