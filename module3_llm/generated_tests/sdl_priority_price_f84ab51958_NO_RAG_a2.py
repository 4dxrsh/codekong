from billing import priority_price

def test_priority_price_with_surcharge():
    amount = 100.0
    expected = round(amount * (1 + PRIORITY_SURCHARGE), 2)
    assert priority_price(amount) == expected, f"Expected {expected}, got {priority_price(amount)}"