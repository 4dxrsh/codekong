from billing import bulk_discount

def test_bulk_discount_below_first_break():
    assert bulk_discount(5) == 0.0, "Should return 0.0 if quantity is below all breakpoints"