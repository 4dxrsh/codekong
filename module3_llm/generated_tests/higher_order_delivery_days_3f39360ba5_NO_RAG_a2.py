from shipping import delivery_days

def test_delivery_days_correct():
    assert delivery_days('local') == 2
    assert delivery_days('local', express=True) == 1

def test_delivery_days_mutated():
    assert delivery_days('local') == None, "Expected None for non-express delivery"
    assert delivery_days('local', express=True) == None, "Expected None for express delivery"