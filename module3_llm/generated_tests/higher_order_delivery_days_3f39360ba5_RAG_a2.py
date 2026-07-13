from shipping import delivery_days

def test_delivery_days_correct():
    assert delivery_days('local') == 1
    assert delivery_days('regional') == 3
    assert delivery_days('national') == 6
    assert delivery_days('international') == 11

def test_delivery_days_mutated():
    assert delivery_days('local', express=True) == 1
    assert delivery_days('regional', express=True) == 3
    assert delivery_days('national', express=True) == 6
    assert delivery_days('international', express=True) == 11