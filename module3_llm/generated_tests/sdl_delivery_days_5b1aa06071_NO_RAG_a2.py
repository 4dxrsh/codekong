from shipping import delivery_days

def test_delivery_days_express():
    assert delivery_days('local', True) == 2, "Express delivery should halve the days and round up"