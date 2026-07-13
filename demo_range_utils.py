"""Small numeric utilities — CodeKong demo input.

Deliberately boundary-heavy and side-effect-free: every function is a good
mutation target (deleting a guard line or swapping a comparison changes
behavior on specific, findable inputs), and none needs files, network, or
randomness — so generated tests can always run.
"""


def clamp(x, lo, hi):
    """Clamp x into the inclusive range [lo, hi].

    >>> clamp(5, 0, 10)
    5
    """
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def lerp(a, b, t):
    """Linear interpolation between a and b; t is clamped to [0, 1].

    >>> lerp(0, 10, 0.5)
    5.0
    """
    t = clamp(t, 0.0, 1.0)
    return a + (b - a) * t


def letter_grade(score):
    """Map a 0-100 score to a letter grade (boundaries are inclusive).

    >>> letter_grade(90)
    'A'
    """
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def running_total(values):
    """Return the list of cumulative sums of values.

    >>> running_total([1, 2, 3])
    [1, 3, 6]
    """
    totals = []
    acc = 0
    for v in values:
        acc = acc + v
        totals.append(acc)
    return totals
