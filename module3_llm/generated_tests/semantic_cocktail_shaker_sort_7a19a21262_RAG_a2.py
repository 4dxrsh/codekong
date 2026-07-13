from cocktail_shaker_sort import cocktail_shaker_sort

def test_cocktail_shaker_sort():
    # Test with a simple list of integers
    assert cocktail_shaker_sort([0, 5, 2, 3, 2]) == [0, 2, 2, 3, 5], "Failed on [0, 5, 2, 3, 2]"
    
    # Test with an empty list
    assert cocktail_shaker_sort([]) == [], "Failed on []"
    
    # Test with a list containing negative integers
    assert cocktail_shaker_sort([-2, -45, -5]) == [-45, -5, -2], "Failed on [-2, -45, -5]"
    
    # Test with a list containing duplicate elements
    assert cocktail_shaker_sort([3, 3, 3, 3]) == [3, 3, 3, 3], "Failed on [3, 3, 3, 3]"
    
    # Test with a list containing a single element
    assert cocktail_shaker_sort([56]) == [56], "Failed on [56]"
    
    # Test with a list of floating-point numbers
    assert cocktail_shaker_sort([1.1, 3.3, 5.5, 7.7, 2.2, 4.4, 6.6]) == [1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7], "Failed on [1.1, 3.3, 5.5, 7.7, 2.2, 4.4, 6.6]"
    
    # Test with a list of mixed data types (should fail)
    try:
        cocktail_shaker_sort([1, 'a', 3.3])
    except TypeError as e:
        assert str(e) == "Cannot compare types: int and str", "Failed on [1, 'a', 3.3] with expected TypeError"