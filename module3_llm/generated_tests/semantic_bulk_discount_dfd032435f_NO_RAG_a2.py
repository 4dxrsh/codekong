from billing import bulk_discount

def test_bulk_discount_boundary_cases():
    assert bulk_discount(6) == 0.2, "Should return 0.2 for quantity at first break"
    assert bulk_discount(10) == 0.3, "Should return 0.3 for quantity just above second break"
    assert bulk_discount(5) == 0.0, "Should return 0.0 for quantity below first break"
    assert bulk_discount(20) == 0.4, "Should return 0.4 for quantity at third break"
    assert bulk_discount(1) == 0.0, "Should return 0.0 for quantity just above zero"