from insertion_sort import Comparable

def test_comparable_lt():
    # Create instances of Comparable with specific values
    obj1 = Comparable(5)
    obj2 = Comparable(3)

    # The deleted statement in __lt__ would have compared the values
    assert obj1 < obj2, "obj1 should be less than obj2"