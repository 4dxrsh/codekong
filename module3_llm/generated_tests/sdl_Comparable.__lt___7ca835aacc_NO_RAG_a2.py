from insertion_sort import Comparable

def test_comparable_lt():
    a = Comparable(10)
    b = Comparable(20)
    assert not a < b, "Should return False when self is less than other"
    assert a < b, "Should return True when self is greater than other"