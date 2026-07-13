from billing import late_fee

def test_late_fee_over_grace():
    assert late_fee(1000.0, 30) == round(1000.0 * LATE_FEE_PCT, 2)