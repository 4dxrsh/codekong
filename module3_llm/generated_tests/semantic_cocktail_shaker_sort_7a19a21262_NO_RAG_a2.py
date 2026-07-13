from cocktail_shaker_sort import cocktail_shaker_sort

def test_cocktail_shaker_sort():
    # Test with a simple unsorted list
    assert cocktail_shaker_sort([4, 5, 2, 1, 2]) == [1, 2, 2, 4, 5], "Failed on simple unsorted list"

    # Test with an already sorted list
    assert cocktail_shaker_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5], "Failed on already sorted list"

    # Test with a reverse-sorted list
    assert cocktail_shaker_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5], "Failed on reverse-sorted list"

    # Test with an empty list
    assert cocktail_shaker_sort([]) == [], "Failed on empty list"

    # Test with a list containing negative values
    assert cocktail_shaker_sort([-4, -5, -24, -7, -11]) == [-24, -11, -7, -5, -4], "Failed on list with negative values"

    # Test with a list containing duplicates
    assert cocktail_shaker_sort([2, 2, 2, 2, 2]) == [2, 2, 2, 2, 2], "Failed on list with duplicates"

    # Test with a tuple (should raise TypeError)
    try:
        cocktail_shaker_sort((-4, -5, -24, -7, -11))
    except TypeError as e:
        assert str(e) == "'tuple' object does not support item assignment", "Failed on tuple input"