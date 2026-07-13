from billing import member_price

def test_member_price_off_by_one():
    assert member_price(100.0, "bronze") == 95.0, "Bronze tier should apply a 5% discount"
    assert member_price(200.0, "silver") == 180.0, "Silver tier should apply a 10% discount"
    assert member_price(50.0, "gold") == 45.0, "Gold tier should apply a 15% discount"
    assert member_price(0.0, "bronze") == 0.0, "Zero amount should return zero"
    assert member_price(-100.0, "bronze") == -95.0, "Negative amount should be handled correctly"