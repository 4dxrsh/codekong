from billing import member_price

def test_member_price_off_by_one():
    assert member_price(100.0, "bronze") == 98.0, "Bronze tier should apply a 2% discount"
    assert member_price(50.0, "silver") == 46.5, "Silver tier should apply a 7% discount"
    assert member_price(1000.0, "gold") == 866.0, "Gold tier should apply a 14% discount"
    assert member_price(2000.0, "platinum") == 1760.0, "Platinum tier should apply a 22% discount"
    assert member_price(0.0, "bronze") == 0.0, "Zero amount should return zero"
    assert member_price(-50.0, "silver") == -53.25, "Negative amount should handle correctly"