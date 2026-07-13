from cocktail_shaker_sort import cocktail_shaker_sort

def test_cocktail_shaker_sort():
    # Test with an empty list
    assert cocktail_shaker_sort([]) == [], "Failed on empty list"

    # Test with a single element
    assert cocktail_shaker_sort([1]) == [1], "Failed on single element"

    # Test with already sorted list
    assert cocktail_shaker_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5], "Failed on already sorted list"

    # Test with reverse-sorted list
    assert cocktail_shaker_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5], "Failed on reverse-sorted list"

    # Test with negative values
    assert cocktail_shaker_sort([-4, -5, -24, -7, -11]) == [-24, -11, -7, -5, -4], "Failed on negative values"

    # Test with duplicates
    assert cocktail_shaker_sort([1, 2, 2, 4, 5]) == [1, 2, 2, 4, 5], "Failed on list with duplicates"

    # Test with floating-point numbers
    assert cocktail_shaker_sort([0.1, -2.4, 4.4, 2.2]) == [-2.4, 0.1, 2.2, 4.4], "Failed on list of floats"