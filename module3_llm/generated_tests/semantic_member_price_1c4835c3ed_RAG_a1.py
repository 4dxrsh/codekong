from billing import member_price

def test_member_price_off_by_one():
    assert member_price(100.0, "bronze") == 98.0, "Bronze tier should apply a 2% discount"
    assert member_price(100.0, "silver") == 93.0, "Silver tier should apply a 7% discount"
    assert member_price(100.0, "gold") == 86.0, "Gold tier should apply a 14% discount"
    assert member_price(100.0, "platinum") == 78.0, "Platinum tier should apply a 22% discount"
    assert member_price(0.0, "bronze") == 0.0, "Zero amount should return zero"
    assert member_price(-100.0, "bronze") == -98.0, "Negative amount should still be discounted"