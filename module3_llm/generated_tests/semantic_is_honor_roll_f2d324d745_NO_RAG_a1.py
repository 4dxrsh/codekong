from grading import is_honor_roll

def test_is_honor_roll():
    # Correct implementation should return True for GPA exactly equal to HONOR_GPA
    assert is_honor_roll(3.5) == True, "GPA 3.5 should qualify for honor roll"
    
    # Buggy implementation will return False for GPA exactly equal to HONOR_GPA
    assert is_honor_roll(3.0) == False, "GPA 3.0 should not qualify for honor roll"
    
    # Edge case: very close to the threshold but below it
    assert is_honor_roll(2.99999) == False, "GPA slightly below 3.0 should not qualify"
    
    # Edge case: exactly at the threshold
    assert is_honor_roll(3.0) == False, "GPA exactly 3.0 should not qualify"
    
    # Edge case: above the threshold
    assert is_honor_roll(3.00001) == True, "GPA slightly above 3.0 should qualify"