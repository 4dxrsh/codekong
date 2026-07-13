from demo_range_utils import clamp

def test_clamp_with_deleted_return():
    assert clamp(5, 0, 10) == 5, "Should return x when it is within the range"
    assert clamp(-1, 0, 10) == 0, "Should return lo when x is less than lo"
    assert clamp(11, 0, 10) == 10, "Should return hi when x is greater than hi"