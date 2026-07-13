from grading import letter_grade

def test_letter_grade_off_by_one():
    assert letter_grade(89) == "B", "Score at cutoff should get correct grade"
    assert letter_grade(75) == "C", "Score just below cutoff should not get higher grade"
    assert letter_grade(63) == "D", "Score just above cutoff should not get lower grade"
    assert letter_grade(0) == "F", "Score at lowest cutoff should get correct grade"