from billing import late_fee

def test_late_fee_off_by_one():
    assert late_fee(1000.0, 30) == 0.0, "Late fee should be 0 within grace period"
    assert late_fee(1000.0, 31) == round(1000.0 * 0.015, 2), "Late fee should be charged after grace period"
    assert late_fee(0.0, 30) == 0.0, "Late fee should be 0 for zero balance within grace period"
    assert late_fee(0.0, 31) == 0.0, "Late fee should be 0 for zero balance after grace period"
    assert late_fee(-1000.0, 30) == 0.0, "Late fee should be 0 for negative balance within grace period"
    assert late_fee(-1000.0, 31) == round(-1000.0 * 0.015, 2), "Late fee should be charged after grace period for negative balance"