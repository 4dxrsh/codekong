from shipping import delivery_days

def test_delivery_days_express():
    assert delivery_days('local', express=True) == 2, "Local express should be 2 days"
    assert delivery_days('regional', express=True) == 2, "Regional express should be 2 days"
    assert delivery_days('national', express=True) == 3, "National express should be 3 days"
    assert delivery_days('international', express=True) == 6, "International express should be 6 days"

def test_delivery_days_standard():
    assert delivery_days('local') == 1, "Local standard should be 1 day"
    assert delivery_days('regional') == 3, "Regional standard should be 3 days"
    assert delivery_days('national') == 6, "National standard should be 6 days"
    assert delivery_days('international') == 11, "International standard should be 11 days"