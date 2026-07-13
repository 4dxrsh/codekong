from shell_sort import shell_sort

def test_shell_sort():
    assert shell_sort([0, 5, 3, 2, 2]) == [0, 2, 2, 3, 5], "Failed on positive integers"
    assert shell_sort([]) == [], "Failed on empty list"
    assert shell_sort([-2, -5, -45]) == [-45, -5, -2], "Failed on negative integers"
    assert shell_sort([1]) == [1], "Failed on single element"
    assert shell_sort([3, 7, 9, 28, 123, -5, 8, -30, -200, 0, 4]) == [-200, -30, -5, 0, 3, 4, 7, 8, 9, 28, 123], "Failed on mixed values"
    assert shell_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5], "Failed on already sorted list"
    assert shell_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5], "Failed on reverse-sorted list"