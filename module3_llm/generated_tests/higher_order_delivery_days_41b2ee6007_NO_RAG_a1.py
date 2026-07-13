from shipping import delivery_days

def test_delivery_days_correct():
    assert delivery_days("local") == 3
    assert delivery_days("local", express=True) == 2

def test_delivery_days_mutated():
    assert delivery_days("local") is None, "Should return days but returns None"
    assert delivery_days("local", express=True) is None, "Should return days but returns None"