from grading import letter_grade

def test_letter_grade_off_by_one():
    assert letter_grade(80) == 'B'  # Correct grade for score 80
    assert letter_grade(79) == 'C'  # Incorrect grade for score 79, should be 'D'
    assert letter_grade(60) == 'F'  # Correct grade for score 60
    assert letter_grade(59) == 'F'  # Incorrect grade for score 59, should be 'E'