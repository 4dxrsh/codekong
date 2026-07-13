from billing import late_fee

def test_late_fee_off_by_one():
    LATE_FEE_GRACE_DAYS = 5
    assert late_fee(1000.0, 5) == 0.0, "Late fee should be 0 within grace period"
    assert late_fee(1000.0, 6) != 0.0, "Late fee should not be 0 after grace period"
    assert late_fee(0.0, 5) == 0.0, "Late fee on zero balance should always be 0"
    assert late_fee(-1000.0, 5) == 0.0, "Negative balance should still have no late fee within grace period"
    assert late_fee(1000.0, -1) == 0.0, "Negative days overdue should still have no late fee"