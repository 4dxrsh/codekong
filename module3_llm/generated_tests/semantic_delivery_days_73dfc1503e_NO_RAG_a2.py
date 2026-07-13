from shipping import delivery_days

def test_delivery_days_correctness():
    assert delivery_days('zone1', express=False) == 2, "Test for non-express delivery in a valid zone"
    assert delivery_days('zone1', express=True) == 3, "Test for express delivery in a valid zone"
    assert delivery_days('zone2', express=False) == 4, "Test for non-express delivery in another valid zone"
    assert delivery_days('zone2', express=True) == 6, "Test for express delivery in another valid zone"
    assert delivery_days('zone3', express=False) == 5, "Test for non-express delivery in a different valid zone"
    assert delivery_days('zone3', express=True) == 8, "Test for express delivery in a different valid zone"

def test_delivery_days_edge_cases():
    assert delivery_days('zone1', express=False) == 2, "Edge case: minimum days for non-express delivery"
    assert delivery_days('zone1', express=True) == 3, "Edge case: minimum days for express delivery"
    assert delivery_days('zone4', express=False) == 6, "Edge case: maximum days for non-express delivery"
    assert delivery_days('zone4', express=True) == 9, "Edge case: maximum days for express delivery"

def test_delivery_days_invalid_zone():
    try:
        delivery_days('invalid_zone', express=False)
    except KeyError as e:
        assert str(e) == "'invalid_zone'", "Test for handling invalid zone input"