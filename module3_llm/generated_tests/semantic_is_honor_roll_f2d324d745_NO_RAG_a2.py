from grading import is_honor_roll

def test_is_honor_roll():
    HONOR_GPA = 3.8
    assert is_honor_roll(HONOR_GPA) == True, f"GPA {HONOR_GPA} should qualify for honor roll"
    assert is_honor_roll(HONOR_GPA - 0.1) == False, f"GPA {HONOR_GPA - 0.1} should not qualify for honor roll"
    assert is_honor_roll(3.5) == True, f"GPA 3.5 should qualify for honor roll"
    assert is_honor_roll(3.49) == False, f"GPA 3.49 should not qualify for honor roll"
    assert is_honor_roll(0) == False, "GPA 0 should not qualify for honor roll"
    assert is_honor_roll(-1) == False, "Negative GPA should not qualify for honor roll"