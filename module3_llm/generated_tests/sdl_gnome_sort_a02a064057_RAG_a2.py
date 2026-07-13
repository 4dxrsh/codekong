from gnome_sort import gnome_sort

def test_gnome_sort_empty_list():
    assert gnome_sort([]) == [], "Empty list should return an empty list"

def test_gnome_sort_single_element():
    assert gnome_sort([5]) == [5], "Single element list should return the same list"

def test_gnome_sort_sorted_list():
    assert gnome_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5], "Already sorted list should remain unchanged"

def test_gnome_sort_reversed_list():
    assert gnome_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5], "Reversed list should be sorted"

def test_gnome_sort_with_duplicates():
    assert gnome_sort([3, 2, 2, 1]) == [1, 2, 2, 3], "List with duplicates should be sorted"