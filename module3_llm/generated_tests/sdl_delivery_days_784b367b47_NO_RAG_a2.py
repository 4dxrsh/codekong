from shipping import delivery_days

def test_delivery_days_with_zone():
    assert delivery_days('local') == 3
    assert delivery_days('international', express=True) == 1