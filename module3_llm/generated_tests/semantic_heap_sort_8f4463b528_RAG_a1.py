from heap_sort import heap_sort

def test_heap_sort():
    assert heap_sort([0, 5, 3, 2, 2]) == [0, 2, 2, 3, 5], "Failed on [0, 5, 3, 2, 2]"
    assert heap_sort([]) == [], "Failed on empty list"
    assert heap_sort([-2, -5, -45]) == [-45, -5, -2], "Failed on negative values"
    assert heap_sort([3, 7, 9, 28, 123, -5, 8, -30, -200, 0, 4]) == [-200, -30, -5, 0, 3, 4, 7, 8, 9, 28, 123], "Failed on mixed values"
    assert heap_sort([1, 1, 1, 1, 1]) == [1, 1, 1, 1, 1], "Failed on all equal elements"
    assert heap_sort([-100, -50, 0, 50, 100]) == [-100, -50, 0, 50, 100], "Failed on sorted values"
    assert heap_sort([100, 50, 0, -50, -100]) == [-100, -50, 0, 50, 100], "Failed on reverse-sorted values"