from shipping import delivery_days

def test_delivery_days_with_zone():
    zone = "local"
    assert delivery_days(zone) == 3, f"Expected delivery days for {zone} to be 3"

def test_delivery_days_with_express():
    zone = "local"
    assert delivery_days(zone, express=True) == 2, f"Expected delivery days for {zone} with express to be 2"