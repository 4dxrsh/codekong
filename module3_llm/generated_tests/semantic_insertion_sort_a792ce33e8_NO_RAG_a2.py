from insertion_sort import insertion_sort

def test_insertion_sort():
    # Test with a simple unsorted list
    assert insertion_sort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9], "Failed on simple unsorted list"

    # Test with a reverse-sorted list
    assert insertion_sort([9, 8, 7, 6, 5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5, 6, 7, 8, 9], "Failed on reverse-sorted list"

    # Test with a single element
    assert insertion_sort([42]) == [42], "Failed on single element"

    # Test with an empty list
    assert insertion_sort([]) == [], "Failed on empty list"

    # Test with a list containing negative values
    assert insertion_sort([-5, -1, 0, 3, 7]) == [-5, -1, 0, 3, 7], "Failed on list with negative values"

    # Test with a list already sorted
    assert insertion_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5], "Failed on already sorted list"