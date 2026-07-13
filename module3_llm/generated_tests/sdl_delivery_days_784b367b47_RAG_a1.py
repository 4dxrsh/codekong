from shipping import delivery_days

def test_delivery_days_local_standard():
    assert delivery_days("local") == 1, "Delivery days for local zone should be 1"

def test_delivery_days_regional_express():
    assert delivery_days("regional", express=True) == 2, "Express delivery days for regional zone should be 2"