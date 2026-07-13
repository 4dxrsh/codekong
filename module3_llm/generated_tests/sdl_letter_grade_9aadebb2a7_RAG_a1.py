from demo_range_utils import letter_grade

def test_letter_grade_A():
    assert letter_grade(90) == "A", "Score 90 should return 'A'"
    assert letter_grade(100) == "A", "Score 100 should return 'A'"
    assert letter_grade(89) != "A", "Score below 90 should not return 'A'"