from grading import is_honor_roll

def test_is_honor_roll():
    assert not is_honor_roll(3.5), "Should return False for GPA just below the threshold"
    assert is_honor_roll(3.6), "Should return True for GPA exactly at the threshold"
    assert is_honor_roll(3.7), "Should return True for GPA above the threshold"
    assert not is_honor_roll(-1.0), "Should return False for negative GPA"
    assert not is_honor_roll(0.0), "Should return False for zero GPA"