from cocktail_shaker_sort import cocktail_shaker_sort

def test_cocktail_shaker_sort():
    # Test cases that should pass for the correct implementation
    assert cocktail_shaker_sort([0, 5, 2, 3, 2]) == [0, 2, 2, 3, 5]
    assert cocktail_shaker_sort([]) == []
    assert cocktail_shaker_sort([-2, -45, -5]) == [-45, -5, -2]
    assert cocktail_shaker_sort([-23, 0, 6, -4, 34]) == [-23, -4, 0, 6, 34]
    assert cocktail_shaker_sort([1, 2, 3, 4]) == [1, 2, 3, 4]
    assert cocktail_shaker_sort([3, 3, 3, 3]) == [3, 3, 3, 3]
    assert cocktail_shaker_sort([56]) == [56]

    # Test cases that should fail for the buggy implementation
    assert cocktail_shaker_sort([0, 5, 2, 3, 2]) != sorted([0, 5, 2, 3, 2])
    assert cocktail_shaker_sort([]) != sorted([])
    assert cocktail_shaker_sort([-2, -45, -5]) != sorted([-2, -45, -5])
    assert cocktail_shaker_sort([-23, 0, 6, -4, 34]) != sorted([-23, 0, 6, -4, 34])
    assert cocktail_shaker_sort(['d', 'a', 'b', 'e']) != sorted(['d', 'a', 'b', 'e'])
    assert cocktail_shaker_sort(['z', 'a', 'y', 'b', 'x', 'c']) != ['a', 'b', 'c', 'x', 'y', 'z']
    assert cocktail_shaker_sort([1.1, 3.3, 5.5, 7.7, 2.2, 4.4, 6.6]) != [1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7]
    assert cocktail_shaker_sort([1, 3.3, 5, 7.7, 2, 4.4, 6]) != [1, 2, 3.3, 4.4, 5, 6, 7.7]
    assert cocktail_shaker_sort(['a', 'Z', 'B', 'C', 'A', 'c']) != sorted(['a', 'Z', 'B', 'C', 'A', 'c'])