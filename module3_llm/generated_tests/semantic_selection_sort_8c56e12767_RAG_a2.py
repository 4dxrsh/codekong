from selection_sort import selection_sort

def test_selection_sort():
    assert selection_sort([0, 5, 3, 2, 2]) == [0, 2, 2, 3, 5], "Failed on simple list"
    assert selection_sort([]) == [], "Failed on empty list"
    assert selection_sort([-2, -5, -45]) == [-45, -5, -2], "Failed on negative numbers"
    assert selection_sort([10]) == [10], "Failed on single element"
    assert selection_sort([3, 3, 3, 3]) == [3, 3, 3, 3], "Failed on duplicates"
    assert selection_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5], "Failed on reverse-sorted list"