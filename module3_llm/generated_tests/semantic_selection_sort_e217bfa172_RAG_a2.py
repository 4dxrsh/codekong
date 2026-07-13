from selection_sort import selection_sort

def test_selection_sort():
    assert selection_sort([0, 5, 3, 2, 2]) == [0, 2, 2, 3, 5], "Failed on [0, 5, 3, 2, 2]"
    assert selection_sort([]) == [], "Failed on empty list"
    assert selection_sort([-2, -5, -45]) == [-45, -5, -2], "Failed on negative values"
    assert selection_sort([1, 2, 3, 4]) == [1, 2, 3, 4], "Failed on already sorted list"
    assert selection_sort([4, 3, 2, 1]) == [1, 2, 3, 4], "Failed on reverse-sorted list"
    assert selection_sort([5, 5, 5, 5]) == [5, 5, 5, 5], "Failed on all elements equal"