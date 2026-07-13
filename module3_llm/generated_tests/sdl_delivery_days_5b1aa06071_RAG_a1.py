from shipping import delivery_days

def test_delivery_days_express():
    zone = "regional"
    express = True
    expected_days = (3 + 1) // 2
    assert delivery_days(zone, express) == expected_days, f"Expected {expected_days}, got {delivery_days(zone, express)}"