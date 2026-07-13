from comb_sort import comb_sort

def test_comb_sort():
    assert comb_sort([0, 5, 3, 2, 2]) == [0, 2, 2, 3, 5], "Failed on simple list"
    assert comb_sort([]) == [], "Failed on empty list"
    assert comb_sort([99, 45, -7, 8, 2, 0, -15, 3]) == [-15, -7, 0, 2, 3, 8, 45, 99], "Failed on mixed list"
    assert comb_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5], "Failed on already sorted list"
    assert comb_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5], "Failed on reverse-sorted list"
    assert comb_sort([-10, -5, 0, 5, 10]) == [-10, -5, 0, 5, 10], "Failed on negative and positive numbers"
    assert comb_sort([10] * 10) == [10] * 10, "Failed on list with duplicates"