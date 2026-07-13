from billing import bulk_discount

def test_bulk_discount_above_first_break():
    assert bulk_discount(10) == 0.1, "Should return 0.1 for quantity >= 5"