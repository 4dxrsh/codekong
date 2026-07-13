from grading import letter_grade

def test_letter_grade_off_by_one():
    assert letter_grade(88) == 'B', "Score at cutoff should get correct grade"
    assert letter_grade(76) == 'C', "Score at cutoff should get correct grade"
    assert letter_grade(64) == 'D', "Score at cutoff should get correct grade"
    assert letter_grade(52) == 'F', "Score at cutoff should get correct grade"
    assert letter_grade(0) == 'F', "Score at cutoff should get correct grade"