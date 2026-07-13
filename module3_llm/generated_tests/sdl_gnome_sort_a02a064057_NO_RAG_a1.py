from gnome_sort import gnome_sort

def test_gnome_sort_with_single_element():
    assert gnome_sort([42]) == [42], "Single element list should return the same list"

def test_gnome_sort_with_empty_list():
    assert gnome_sort([]) == [], "Empty list should return an empty list"

def test_gnome_sort_with_sorted_list():
    assert gnome_sort([1, 2, 3, 4]) == [1, 2, 3, 4], "Already sorted list should remain unchanged"

def test_gnome_sort_with_reversed_list():
    assert gnome_sort([4, 3, 2, 1]) == [1, 2, 3, 4], "Reversed list should be sorted"

def test_gnome_sort_with_mixed_elements():
    assert gnome_sort([3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]) == [1, 1, 2, 3, 3, 4, 5, 5, 5, 6, 9], "Mixed elements should be sorted"