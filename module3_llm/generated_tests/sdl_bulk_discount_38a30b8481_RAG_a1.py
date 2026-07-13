from billing import bulk_discount

def test_bulk_discount_no_breaks():
    assert bulk_discount(1) == 0.0