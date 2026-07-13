from gnome_sort import gnome_sort

def test_gnome_sort_empty_list():
    assert gnome_sort([]) == [], "Empty list should return an empty list"

def test_gnome_sort_single_element():
    assert gnome_sort([42]) == [42], "Single element list should return the same list"