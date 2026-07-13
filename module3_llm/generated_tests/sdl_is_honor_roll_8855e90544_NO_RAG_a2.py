from grading import is_honor_roll

def test_is_honor_roll_passing():
    assert is_honor_roll(3.8) == True, "Should return True for GPA >= HONOR_GPA"

def test_is_honor_roll_failing():
    assert is_honor_roll(3.5) == False, "Should return False for GPA < HONOR_GPA"