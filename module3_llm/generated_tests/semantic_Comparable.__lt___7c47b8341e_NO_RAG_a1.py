from insertion_sort import Comparable

def test_comparable_lt():
    # Test with equal values
    assert not Comparable(5).__lt__(Comparable(5)), "Equal values should return False"
    
    # Test with different values where the current is less
    assert Comparable(3).__lt__(Comparable(4)), "Smaller value should return True"
    
    # Test with different values where the current is greater
    assert not Comparable(7).__lt__(Comparable(6)), "Larger value should return False"
    
    # Test with negative values
    assert Comparable(-2).__lt__(Comparable(0)), "Negative value should return True"
    
    # Test with zero and a positive number
    assert Comparable(0).__lt__(Comparable(1)), "Zero should return True for positive numbers"
    
    # Test with zero and a negative number
    assert not Comparable(0).__lt__(Comparable(-1)), "Zero should return False for negative numbers"