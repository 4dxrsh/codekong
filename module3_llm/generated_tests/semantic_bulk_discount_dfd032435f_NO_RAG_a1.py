from billing import bulk_discount

def test_bulk_discount_boundary_cases():
    assert bulk_discount(0) == 0.0, "Should return 0.0 for quantity 0"
    assert bulk_discount(1) == 0.0, "Should return 0.0 for quantity 1"
    assert bulk_discount(5) == 0.0, "Should return 0.0 for quantity below first break"
    assert bulk_discount(6) == 0.2, "Should return 0.2 for quantity at first break"
    assert bulk_discount(7) == 0.3, "Should return 0.3 for quantity above first break but below second break"
    assert bulk_discount(10) == 0.4, "Should return 0.4 for quantity at second break"
    assert bulk_discount(11) == 0.5, "Should return 0.5 for quantity above second break"
    assert bulk_discount(20) == 0.6, "Should return 0.6 for quantity at third break"
    assert bulk_discount(21) == 0.7, "Should return 0.7 for quantity above third break"
    assert bulk_discount(30) == 0.8, "Should return 0.8 for quantity at fourth break"
    assert bulk_discount(31) == 0.9, "Should return 0.9 for quantity above fourth break"
    assert bulk_discount(50) == 1.0, "Should return 1.0 for quantity at fifth break"
    assert bulk_discount(51) == 1.0, "Should return 1.0 for quantity above fifth break"