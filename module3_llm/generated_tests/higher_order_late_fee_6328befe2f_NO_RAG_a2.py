from billing import late_fee

def test_late_fee_within_grace():
    assert late_fee(1000.0, 10) == 0.0

def test_late_fee_after_grace():
    assert late_fee(1000.0, 6) > 0.0