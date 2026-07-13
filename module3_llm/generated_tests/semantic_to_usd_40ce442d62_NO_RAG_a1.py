from billing import to_usd

def test_to_usd_precision():
    assert to_usd(0.45, "USD") == 0.45, "Failed on positive value with precision issue"
    assert to_usd(0.46, "USD") == 0.46, "Failed on positive value with rounding up"
    assert to_usd(0.449, "USD") == 0.44, "Failed on positive value with rounding down"
    assert to_usd(-0.45, "USD") == -0.45, "Failed on negative value with precision issue"
    assert to_usd(-0.46, "USD") == -0.46, "Failed on negative value with rounding up"
    assert to_usd(-0.449, "USD") == -0.44, "Failed on negative value with rounding down"
    assert to_usd(1.0, "USD") == 1.0, "Failed on edge case of 1.0"
    assert to_usd(0.0, "USD") == 0.0, "Failed on edge case of 0.0"