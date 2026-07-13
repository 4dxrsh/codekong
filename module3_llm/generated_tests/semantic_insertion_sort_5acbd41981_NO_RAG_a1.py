from insertion_sort import insertion_sort

def test_insertion_sort():
    assert insertion_sort([0, 5, 3, 2, 2]) == [0, 2, 2, 3, 5], "Failed on simple list"
    assert insertion_sort([]) == [], "Failed on empty list"
    assert insertion_sort([-2, -5, -45]) == [-45, -5, -2], "Failed on negative numbers"
    assert insertion_sort(['d', 'a', 'b', 'e', 'c']) == ['a', 'b', 'c', 'd', 'e'], "Failed on strings"
    assert insertion_sort([1]) == [1], "Failed on single element list"
    assert insertion_sort([2, 1]) == [1, 2], "Failed on reverse sorted list with two elements"