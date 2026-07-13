from shipping import delivery_days

def test_delivery_days_express():
    zone = "regional"
    assert delivery_days(zone, express=True) == 2, "Express should halve the delivery time"

def test_delivery_days_standard():
    zone = "national"
    assert delivery_days(zone, express=False) == 6, "Standard should return the original delivery time"