from shipping import delivery_days

def test_delivery_days_without_express():
    zone = "local"
    assert delivery_days(zone) == 1, f"Expected 1 for zone '{zone}', got {delivery_days(zone)}"