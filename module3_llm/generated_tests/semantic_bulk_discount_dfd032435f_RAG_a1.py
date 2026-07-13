from billing import bulk_discount

def test_bulk_discount_boundary_cases():
    assert bulk_discount(0) == 0.0, "Should return 0.0 for quantity 0"
    assert bulk_discount(9) == 0.0, "Should return 0.0 for quantity just below first break"
    assert bulk_discount(10) == 0.04, "Should return 0.04 for quantity at first break"
    assert bulk_discount(50) == 0.11, "Should return 0.11 for quantity at second break"
    assert bulk_discount(99) == 0.11, "Should return 0.11 for quantity just below second break"
    assert bulk_discount(100) == 0.18, "Should return 0.18 for quantity at third break"
    assert bulk_discount(250) == 0.18, "Should return 0.18 for quantity above all breaks"