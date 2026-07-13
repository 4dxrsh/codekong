from insertion_sort import Comparable

def test_comparable_lt():
    # Test with equal values
    assert Comparable(5).__lt__(Comparable(5)) == False, "Equal values should not be less than each other"
    
    # Test with different values
    assert Comparable(3).__lt__(Comparable(4)) == True, "Smaller value should be less than larger value"
    assert Comparable(4).__lt__(Comparable(3)) == False, "Larger value should not be less than smaller value"
    
    # Test with negative values
    assert Comparable(-2).__lt__(Comparable(-1)) == True, "Negative value closer to zero should be less than negative value further from zero"
    assert Comparable(-1).__lt__(Comparable(-2)) == False, "Negative value further from zero should not be less than negative value closer to zero"
    
    # Test with boundary values
    assert Comparable(0).__lt__(Comparable(1)) == True, "Zero should be less than positive value"
    assert Comparable(1).__lt__(Comparable(0)) == False, "Positive value should not be less than zero"