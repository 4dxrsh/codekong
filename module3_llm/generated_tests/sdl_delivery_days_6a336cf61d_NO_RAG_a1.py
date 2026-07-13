from shipping import delivery_days

def test_delivery_days_standard():
    assert delivery_days("local") == 3, "Standard delivery should return 3 days for 'local' zone"

def test_delivery_days_express():
    assert delivery_days("local", express=True) == 2, "Express delivery should return 2 days for 'local' zone"