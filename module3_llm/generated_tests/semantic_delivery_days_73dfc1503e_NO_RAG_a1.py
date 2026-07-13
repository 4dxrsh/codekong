from shipping import delivery_days

def test_delivery_days_correctness():
    assert delivery_days("zone1", express=False) == 5, "Non-express delivery should be correct"
    assert delivery_days("zone2", express=True) == 3, "Express delivery should be correct"

def test_delivery_days_edge_cases():
    assert delivery_days("zone1", express=True) == 3, "Edge case: Express delivery with odd days"
    assert delivery_days("zone2", express=False) == 5, "Edge case: Non-express delivery with even days"

def test_delivery_days_negative_input():
    try:
        delivery_days(-1, express=False)
    except ValueError as e:
        assert str(e) == "Invalid zone", "Negative input should raise ValueError"