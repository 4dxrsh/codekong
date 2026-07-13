from grading import letter_grade

def test_letter_grade_off_by_one():
    assert letter_grade(90) == "A"  # Correct grade for score >= 90
    assert letter_grade(89) == "B"  # Incorrect grade for score > 89, should be "A"
    assert letter_grade(70) == "C"  # Correct grade for score >= 70
    assert letter_grade(69) == "D"  # Incorrect grade for score > 69, should be "C"
    assert letter_grade(50) == "F"  # Correct grade for score < 50