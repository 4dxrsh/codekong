from billing import late_fee

def test_late_fee_off_by_one():
    assert late_fee(1000.0, 10) == 0.0, "Late fee should be 0 within grace period"
    assert late_fee(1000.0, LATE_FEE_GRACE_DAYS) == 0.0, "Late fee should be 0 on the grace day boundary"
    assert late_fee(1000.0, LATE_FEE_GRACE_DAYS + 1) != 0.0, "Late fee should be non-zero after grace period"
    assert late_fee(1000.0, -1) == 0.0, "Negative days overdue should still be within grace period"
    assert late_fee(1000.0, 0) == 0.0, "Zero days overdue should still be within grace period"