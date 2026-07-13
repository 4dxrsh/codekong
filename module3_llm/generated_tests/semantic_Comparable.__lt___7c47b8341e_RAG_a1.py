from insertion_sort import Comparable

def test_comparable_lt():
    # Edge case: empty input
    assert not Comparable().__lt__(Comparable())
    
    # Boundary case: single element
    assert not Comparable(1).__lt__(Comparable(1))
    assert Comparable(1).__lt__(Comparable(2))
    assert not Comparable(2).__lt__(Comparable(1))
    
    # Normal case: different values
    assert Comparable(3).__lt__(Comparable(4))
    assert not Comparable(4).__lt__(Comparable(3))
    
    # Negative values
    assert Comparable(-5).__lt__(Comparable(-3))
    assert not Comparable(-3).__lt__(Comparable(-5))
    
    # Duplicate values
    assert not Comparable(7).__lt__(Comparable(7))