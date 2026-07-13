from insertion_sort import insertion_sort

def test_insertion_sort():
    # Test with an empty list
    assert insertion_sort([]) == [], "Failed on empty list"

    # Test with a single element
    assert insertion_sort([1]) == [1], "Failed on single element"

    # Test with already sorted list
    assert insertion_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5], "Failed on already sorted list"

    # Test with reverse-sorted list
    assert insertion_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5], "Failed on reverse-sorted list"

    # Test with negative values
    assert insertion_sort([-5, -4, -3, -2, -1]) == [-5, -4, -3, -2, -1], "Failed on negative values"

    # Test with duplicates
    assert insertion_sort([3, 2, 2, 1]) == [1, 2, 2, 3], "Failed on list with duplicates"

    # Test with boundary conditions
    assert insertion_sort([0, -1, 1]) == [-1, 0, 1], "Failed on boundary conditions"