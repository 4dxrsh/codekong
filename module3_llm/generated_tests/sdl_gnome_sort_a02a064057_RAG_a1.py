from gnome_sort import gnome_sort

def test_gnome_sort():
    assert gnome_sort([0, 5, 3, 2, 2]) == [0, 2, 2, 3, 5], "Failed on sorted list"
    assert gnome_sort([]) == [], "Failed on empty list"
    assert gnome_sort([-2, -5, -45]) == [-45, -5, -2], "Failed on negative numbers"
    assert gnome_sort([3, 7, 9, 28, 123, -5, 8, -30, -200, 0, 4]) == [-200, -30, -5, 0, 3, 4, 7, 8, 9, 28, 123], "Failed on mixed list"