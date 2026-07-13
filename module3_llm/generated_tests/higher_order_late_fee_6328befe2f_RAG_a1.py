from billing import late_fee

def test_late_fee_within_grace():
    assert late_fee(1000.0, 30) == 0.0, "Should return 0.0 within grace period"

def test_late_fee_after_grace():
    assert late_fee(1000.0, 31) == 15.0, "Should return late fee after grace period"

def test_late_fee_boundary():
    assert late_fee(1000.0, 30) == 0.0 and late_fee(1000.0, 31) == 15.0, "Should handle boundary condition"