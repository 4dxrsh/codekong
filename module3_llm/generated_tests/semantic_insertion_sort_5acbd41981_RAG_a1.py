from insertion_sort import insertion_sort

def test_insertion_sort():
    assert insertion_sort([0, 5, 3, 2, 2]) == [0, 2, 2, 3, 5], "Failed on positive integers"
    assert insertion_sort([]) == [], "Failed on empty list"
    assert insertion_sort([-2, -5, -45]) == [-45, -5, -2], "Failed on negative integers"
    assert insertion_sort(['d', 'a', 'b', 'e', 'c']) == ['a', 'b', 'c', 'd', 'e'], "Failed on strings"
    assert insertion_sort([10]) == [10], "Failed on single element"
    assert insertion_sort([3, 2, 1]) == [1, 2, 3], "Failed on reverse-sorted list"
    assert insertion_sort([1, 2, 3]) == [1, 2, 3], "Failed on already-sorted list"