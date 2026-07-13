from selection_sort import selection_sort

def test_selection_sort():
    assert selection_sort([0, 5, 3, 2, 2]) == [0, 2, 2, 3, 5], "Failed on a typical case"
    assert selection_sort([]) == [], "Failed on an empty list"
    assert selection_sort([-2, -5, -45]) == [-45, -5, -2], "Failed on negative numbers"
    assert selection_sort([1]) == [1], "Failed on a single-element list"
    assert selection_sort([3, 2, 1]) == [1, 2, 3], "Failed on reverse-sorted list"
    assert selection_sort([1, 2, 3]) == [1, 2, 3], "Failed on already-sorted list"