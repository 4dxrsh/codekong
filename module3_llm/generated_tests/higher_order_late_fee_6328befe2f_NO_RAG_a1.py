from billing import late_fee

def test_late_fee_boundary():
    # Test boundary for off-by-one error in grace period comparison
    assert late_fee(1000.0, 5) == 0.0, "Should return 0.0 within grace period"
    assert late_fee(1000.0, 6) > 0.0, "Should return a late fee after grace period"

def test_late_fee_combined():
    # Test combined effect of both mutations
    assert late_fee(1000.0, 5) == 0.0, "Should return 0.0 within grace period"
    assert late_fee(1000.0, 6) > 0.0, "Should return a late fee after grace period"