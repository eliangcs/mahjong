'''
General utility functions.

'''
import bisect
import itertools


def index(a, x):
    '''Binary search. Locate the leftmost value == x.'''
    i = bisect.bisect_left(a, x)
    if i != len(a) and a[i] == x:
        return i
    return -1


def find_lt(a, x):
    '''Binary search. Find rightmost value < x.'''
    i = bisect.bisect_left(a, x)
    if i:
        return a[i - 1]
    raise ValueError


def find_le(a, x):
    '''Binary search. Find rightmost value <= x.'''
    i = bisect.bisect_right(a, x)
    if i:
        return a[i - 1]
    raise ValueError


def find_gt(a, x):
    '''Binary search. Find leftmost value > x'''
    i = bisect.bisect_right(a, x)
    if i != len(a):
        return a[i]
    raise ValueError


def find_ge(a, x):
    '''Binary search. Find leftmost item >= x.'''
    i = bisect.bisect_left(a, x)
    if i != len(a):
        return a[i]
    raise ValueError


def combs_with_comp(seq, r):
    '''
    Similar to itertools.combinations(), but with complement returned.

    Example:
    >>> combs_with_comp([1, 2, 3], 1)
    [([1], [2, 3]), ([2], [1, 3]), ([3], [1, 2])]

    '''
    indices = range(0, len(seq))
    for comb in itertools.combinations(indices, r):
        comp = filter(lambda a: a not in comb, indices)
        yield [seq[i] for i in comb], [seq[i] for i in comp]
