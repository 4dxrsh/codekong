from grading import is_honor_roll

def test_is_honor_roll_pass():
    assert is_honor_roll(3.7) == True, "Should return True for GPA >= HONOR_GPA"

def test_is_honor_roll_fail():
    assert is_honor_roll(3.5) == False, "Should return False for GPA < HONOR_GPA"