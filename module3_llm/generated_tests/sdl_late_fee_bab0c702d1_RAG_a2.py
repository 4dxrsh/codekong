from billing import late_fee

def test_late_fee_over_grace():
    assert late_fee(1000.0, 35) == round(1000.0 * 0.015, 2)