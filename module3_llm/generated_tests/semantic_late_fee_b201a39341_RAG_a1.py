from billing import late_fee

def test_late_fee_off_by_one():
    assert late_fee(1000.0, 30) == 0.0, "Should be within grace period"
    assert late_fee(1000.0, 31) != 0.0, "Should be after grace period"
    assert late_fee(500.0, -1) == 0.0, "Negative days overdue should still be within grace period"
    assert late_fee(500.0, 0) == 0.0, "Zero days overdue should still be within grace period"
    assert late_fee(500.0, LATE_FEE_GRACE_DAYS) == 0.0, "On the boundary of grace period"