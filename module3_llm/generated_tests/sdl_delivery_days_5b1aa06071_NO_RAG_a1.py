from shipping import delivery_days

def test_delivery_days_express():
    zone = "local"
    express = True
    assert delivery_days(zone, express) == 2, "Express delivery should halve the days and round up"

def test_delivery_days_standard():
    zone = "local"
    express = False
    assert delivery_days(zone, express) == 3, "Standard delivery should return the original number of days"