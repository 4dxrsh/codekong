from grading import is_passing

def test_is_passing_with_pass_mark():
    score = rates.PASS_MARK
    assert is_passing(score) == True, f"Expected True for score {score}, but got False"

def test_is_passing_below_pass_mark():
    score = rates.PASS_MARK - 1
    assert is_passing(score) == False, f"Expected False for score {score}, but got True"