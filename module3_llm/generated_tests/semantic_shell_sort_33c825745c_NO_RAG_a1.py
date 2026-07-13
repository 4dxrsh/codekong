from shell_sort import shell_sort

def test_shell_sort():
    assert shell_sort([0, 5, 3, 2, 2]) == [0, 2, 2, 3, 5], "Failed on simple list"
    assert shell_sort([]) == [], "Failed on empty list"
    assert shell_sort([-2, -5, -45]) == [-45, -5, -2], "Failed on negative numbers"
    assert shell_sort([1]) == [1], "Failed on single element"
    assert shell_sort([3, 2, 1]) == [1, 2, 3], "Failed on reverse sorted list"
    assert shell_sort([1, 2, 3]) == [1, 2, 3], "Failed on already sorted list"
    assert shell_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5], "Failed on descending order"
    assert shell_sort([1, 3, 2, 5, 4]) == [1, 2, 3, 4, 5], "Failed on mixed order"