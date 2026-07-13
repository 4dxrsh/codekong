from billing import bulk_discount

def test_bulk_discount_no_breaks():
    assert bulk_discount(10) == 0.0, "Should return 0.0 if quantity is below all breakpoints"