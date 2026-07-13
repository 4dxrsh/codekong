from merge_sort import merge

def test_merge():
    assert merge([1], [2]) == [1, 2], "Single element lists"
    assert merge([2], [1]) == [1, 2], "Reverse single element lists"
    assert merge([], [1, 2]) == [1, 2], "Empty left list"
    assert merge([1, 2], []) == [1, 2], "Empty right list"
    assert merge([1, 3], [2, 4]) == [1, 2, 3, 4], "General case"
    assert merge([2, 4], [1, 3]) == [1, 2, 3, 4], "Reverse general case"
    assert merge([1, 1, 1], [1, 1, 1]) == [1, 1, 1, 1, 1, 1], "Duplicates"
    assert merge([-1, 0, 1], [-2, -1, 0]) == [-2, -1, -1, 0, 0, 1], "Negative values"
    assert merge([1, 3, 5], [2, 4, 6]) == [1, 2, 3, 4, 5, 6], "Already sorted"
    assert merge([6, 4, 2], [5, 3, 1]) == [1, 2, 3, 4, 5, 6], "Reverse-sorted"