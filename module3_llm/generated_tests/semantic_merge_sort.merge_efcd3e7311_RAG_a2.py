from merge_sort import merge_sort

def test_merge():
    assert merge_sort([0, 5, 3, 2, 2]) == [0, 2, 2, 3, 5], "Failed on positive integers"
    assert merge_sort([]) == [], "Failed on empty list"
    assert merge_sort([-2, -5, -45]) == [-45, -5, -2], "Failed on negative integers"
    assert merge_sort([1]) == [1], "Failed on single element"
    assert merge_sort([3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]) == [1, 1, 2, 3, 3, 4, 5, 5, 5, 6, 9], "Failed on mixed integers"