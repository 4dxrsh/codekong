from shipping import delivery_days

def test_delivery_days_express():
    assert delivery_days("zone1", express=True) == 2, "Express should halve the days and round up"
    assert delivery_days("zone2", express=True) == 3, "Express should halve the days and round up"

def test_delivery_days_standard():
    assert delivery_days("zone1") == 4, "Standard should return the original days"
    assert delivery_days("zone2") == 5, "Standard should return the original days"