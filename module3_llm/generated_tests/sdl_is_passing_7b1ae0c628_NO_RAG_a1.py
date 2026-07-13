from grading import is_passing

def test_is_passing_with_pass_mark():
    assert not is_passing(50), "Should return False for score below PASS_MARK"

def test_is_passing_with_pass_mark():
    assert is_passing(60), "Should return True for score equal to PASS_MARK"