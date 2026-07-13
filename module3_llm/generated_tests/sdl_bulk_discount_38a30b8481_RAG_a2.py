from billing import bulk_discount

def test_bulk_discount_below_first_break():
    assert bulk_discount(5) == 0.18, "Should return 0.18 for quantity below first break"