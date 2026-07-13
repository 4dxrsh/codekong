from shipping import delivery_days

def test_delivery_days_local_standard():
    assert delivery_days("local") == 1, "Failed for local zone with standard delivery"

def test_delivery_days_regional_express():
    assert delivery_days("regional", express=True) == 2, "Failed for regional zone with express delivery"