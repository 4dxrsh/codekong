from billing import to_usd

def test_to_usd_precision():
    assert to_usd(0.45, "USD") == 0.45, "Failed on positive value with precision issue"
    assert to_usd(0.55, "USD") == 0.55, "Failed on positive value with precision issue"
    assert to_usd(-0.45, "USD") == -0.45, "Failed on negative value with precision issue"
    assert to_usd(-0.55, "USD") == -0.55, "Failed on negative value with precision issue"
    assert to_usd(1.23456789, "USD") == 1.23, "Failed on large positive value with precision issue"
    assert to_usd(-1.23456789, "USD") == -1.23, "Failed on large negative value with precision issue"
    assert to_usd(0.0, "USD") == 0.0, "Failed on zero value with precision issue"