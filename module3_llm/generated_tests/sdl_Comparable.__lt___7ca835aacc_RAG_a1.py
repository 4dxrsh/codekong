from insertion_sort import Comparable

def test_comparable_lt():
    # Create instances of Comparable with different values
    obj1 = Comparable(5)
    obj2 = Comparable(3)

    # The deleted statement was responsible for setting up the comparison logic
    assert obj1 < obj2, "obj1 should be less than obj2"