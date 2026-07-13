from insertion_sort import insertion_sort

def test_insertion_sort():
    # Edge case: empty list
    assert insertion_sort([]) == [], "Empty list should remain unchanged"

    # Edge case: single element
    assert insertion_sort([5]) == [5], "Single element list should remain unchanged"

    # Case with negative values
    assert insertion_sort([-2, -5, -45]) == [-45, -5, -2], "Negative values should be sorted correctly"

    # Case where the first element is not at its correct position
    assert insertion_sort([3, 1, 2]) == [1, 2, 3], "First element not at correct position should be sorted correctly"

    # Case with duplicates
    assert insertion_sort([2, 2, 3, 1]) == [1, 2, 2, 3], "Duplicates should be sorted correctly"