from shipping import delivery_days

def test_delivery_days_correctness():
    assert delivery_days("local", express=False) == 1, "Local non-express should be 1 day"
    assert delivery_days("regional", express=False) == 3, "Regional non-express should be 3 days"
    assert delivery_days("national", express=False) == 6, "National non-express should be 6 days"
    assert delivery_days("international", express=False) == 11, "International non-express should be 11 days"

def test_delivery_days_express():
    assert delivery_days("local", express=True) == 2, "Local express should be 2 days"
    assert delivery_days("regional", express=True) == 4, "Regional express should be 4 days"
    assert delivery_days("national", express=True) == 8, "National express should be 8 days"
    assert delivery_days("international", express=True) == 16, "International express should be 16 days"

def test_delivery_days_edge_cases():
    assert delivery_days("", express=False) == 0, "Empty zone should return 0 days"
    assert delivery_days(None, express=False) == 0, "None zone should return 0 days"
    assert delivery_days("local", express=True) != delivery_days("local", express=False), "Express and non-express should differ"

def test_delivery_days_negative_zone():
    try:
        delivery_days("-1", express=False)
    except KeyError as e:
        assert str(e) == "'-1'", "Negative zone should raise KeyError with the zone value"