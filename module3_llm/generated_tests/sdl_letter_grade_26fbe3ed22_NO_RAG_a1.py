from grading import letter_grade

def test_letter_grade_bottom():
    assert letter_grade(0) == "F"