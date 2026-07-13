from insertion_sort import Comparable

def test_comparable_lt():
    # Test with equal values
    assert Comparable(5).__lt__(Comparable(5)) == False, "Equal values should not be less than each other"
    
    # Test with different values where the first is less
    assert Comparable(3).__lt__(Comparable(4)) == True, "3 should be less than 4"
    
    # Test with different values where the first is greater
    assert Comparable(7).__lt__(Comparable(6)) == False, "7 should not be less than 6"
    
    # Test with negative values
    assert Comparable(-2).__lt__(Comparable(-1)) == True, "-2 should be less than -1"
    
    # Test with zero and a positive number
    assert Comparable(0).__lt__(Comparable(1)) == True, "0 should be less than 1"
    
    # Test with zero and a negative number
    assert Comparable(0).__lt__(Comparable(-1)) == False, "0 should not be less than -1"