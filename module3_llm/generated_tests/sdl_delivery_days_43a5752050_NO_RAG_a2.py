from shipping import delivery_days

def test_delivery_days_express():
    zone = 'zone1'
    days = 3
    assert delivery_days(zone, express=True) == (days + 1) // 2, "Express should halve the time and round up"