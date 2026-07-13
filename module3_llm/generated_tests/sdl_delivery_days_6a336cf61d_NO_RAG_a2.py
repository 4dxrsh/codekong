from shipping import delivery_days

def test_delivery_days_standard():
    assert delivery_days('local') == 3, "Standard delivery should return 3 days for 'local' zone"