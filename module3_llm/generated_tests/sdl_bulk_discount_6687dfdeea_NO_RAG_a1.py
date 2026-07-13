from billing import bulk_discount

def test_bulk_discount_above_first_break():
    assert bulk_discount(10) == 0.15, "Should return 0.15 for quantity >= 10"