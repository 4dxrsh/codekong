from merge_sort import merge

def test_merge():
    assert merge([1, 2], [3, 4]) == [1, 2, 3, 4], "Failed on simple ascending lists"
    assert merge([4, 5], [1, 2]) == [1, 2, 4, 5], "Failed on simple descending lists"
    assert merge([], [1, 2]) == [1, 2], "Failed on left empty list"
    assert merge([1, 2], []) == [1, 2], "Failed on right empty list"
    assert merge([1, 3, 5], [2, 4, 6]) == [1, 2, 3, 4, 5, 6], "Failed on interleaved lists"
    assert merge([-1, -2], [-3, -4]) == [-3, -4, -2, -1], "Failed on negative values"
    assert merge([10], [5, 7, 9]) == [5, 7, 9, 10], "Failed on single element list"
    assert merge([1, 2, 3], [4, 5, 6]) == [1, 2, 3, 4, 5, 6], "Failed on already sorted lists"
    assert merge([6, 5, 4], [3, 2, 1]) == [1, 2, 3, 4, 5, 6], "Failed on reverse-sorted lists"