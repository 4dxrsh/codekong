from comb_sort import comb_sort

def test_comb_sort():
    assert comb_sort([0, 5, 3, 2, 2]) == [0, 2, 2, 3, 5], "Failed on positive integers"
    assert comb_sort([]) == [], "Failed on empty list"
    assert comb_sort([-2, -5, -45]) == [-45, -5, -2], "Failed on negative integers"
    assert comb_sort([1]) == [1], "Failed on single element"
    assert comb_sort([3, 2, 1]) == [1, 2, 3], "Failed on reverse-sorted list"
    assert comb_sort([1, 2, 3]) == [1, 2, 3], "Failed on already-sorted list"