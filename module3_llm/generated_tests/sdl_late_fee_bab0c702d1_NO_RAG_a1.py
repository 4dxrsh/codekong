from billing import late_fee

def test_late_fee_within_grace():
    assert late_fee(1000.0, 5) == 0.0, "Late fee should be 0 within grace period"