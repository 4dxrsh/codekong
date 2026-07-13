"""Score-to-grade helpers, using the (non-standard) bands defined in rates.py."""
from rates import GRADE_BANDS, PASS_MARK, HONOR_GPA


def letter_grade(score):
    """Convert a 0-100 score to a letter grade using the course's bands
    (see rates.GRADE_BANDS). A score at or above a band's cutoff earns its
    letter. The cutoffs are NOT the usual 90/80/70/60."""
    for cutoff, letter in GRADE_BANDS:
        if score >= cutoff:
            return letter
    return "F"


def gpa_points(score):
    """Convert a score to 4.0-scale grade points (A=4, B=3, C=2, D=1, F=0),
    derived from its letter grade."""
    mapping = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}
    return mapping[letter_grade(score)]


def is_passing(score):
    """Return True if the score meets the course's minimum passing mark
    (see rates.PASS_MARK)."""
    return score >= PASS_MARK


def is_honor_roll(gpa):
    """Return True if a GPA qualifies for the honor roll (threshold in
    rates.HONOR_GPA)."""
    return gpa >= HONOR_GPA
