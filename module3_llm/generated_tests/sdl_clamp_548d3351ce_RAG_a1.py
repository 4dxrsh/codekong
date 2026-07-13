from demo_range_utils import clamp

def test_clamp_with_negative_value():
    assert clamp(-1, 0, 10) == 0, "Negative value should be clamped to lower bound"