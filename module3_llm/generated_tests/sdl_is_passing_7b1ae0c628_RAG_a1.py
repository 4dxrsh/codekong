from grading import is_passing

def test_is_passing_with_pass_mark():
    score = rates.PASS_MARK
    assert not is_passing(score), f"Expected False for score {score}"

def test_is_passing_above_pass_mark():
    score = rates.PASS_MARK + 1
    assert is_passing(score), f"Expected True for score {score}"