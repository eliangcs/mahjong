import unittest

from mahjong import utils


class TestBinarySearch(unittest.TestCase):

    def test_empty_list(self):
        a = []
        self.assertEqual(utils.index(a, 0), -1)
        self.assertEqual(utils.index(a, 1), -1)

        with self.assertRaises(ValueError):
            utils.find_lt(a, 0)
        with self.assertRaises(ValueError):
            utils.find_le(a, 0)
        with self.assertRaises(ValueError):
            utils.find_gt(a, 0)
        with self.assertRaises(ValueError):
            utils.find_ge(a, 0)

    def test_index(self):
        a = [1, 5, 9, 14, 14, 14, 20, 34, 34, 56, 78]
        self.assertEqual(utils.index(a, 1), 0)
        self.assertEqual(utils.index(a, 14), 3)
        self.assertEqual(utils.index(a, 20), 6)
        self.assertEqual(utils.index(a, 78), 10)
        self.assertEqual(utils.index(a, 0), -1)
        self.assertEqual(utils.index(a, 15), -1)

    def test_find_lt(self):
        a = [1, 5, 9, 14, 14, 14, 20, 34, 34, 56, 78]
        self.assertEqual(utils.find_lt(a, 2), 1)
        self.assertEqual(utils.find_lt(a, 14), 9)
        self.assertEqual(utils.find_lt(a, 20), 14)
        self.assertEqual(utils.find_lt(a, 79), 78)
        with self.assertRaises(ValueError):
            utils.find_lt(a, 0)

    def test_find_le(self):
        a = [1, 5, 9, 14, 14, 14, 20, 34, 34, 56, 78]
        self.assertEqual(utils.find_le(a, 2), 1)
        self.assertEqual(utils.find_le(a, 14), 14)
        self.assertEqual(utils.find_le(a, 20), 20)
        self.assertEqual(utils.find_le(a, 79), 78)
        with self.assertRaises(ValueError):
            utils.find_le(a, 0)

    def test_find_gt(self):
        a = [1, 5, 9, 14, 14, 14, 20, 34, 34, 56, 78]
        self.assertEqual(utils.find_gt(a, 0), 1)
        self.assertEqual(utils.find_gt(a, 2), 5)
        self.assertEqual(utils.find_gt(a, 14), 20)
        self.assertEqual(utils.find_gt(a, 20), 34)
        with self.assertRaises(ValueError):
            utils.find_gt(a, 79)

    def test_find_ge(self):
        a = [1, 5, 9, 14, 14, 14, 20, 34, 34, 56, 78]
        self.assertEqual(utils.find_ge(a, 0), 1)
        self.assertEqual(utils.find_ge(a, 2), 5)
        self.assertEqual(utils.find_ge(a, 14), 14)
        self.assertEqual(utils.find_ge(a, 20), 20)
        with self.assertRaises(ValueError):
            utils.find_ge(a, 79)


class TestCombinations(unittest.TestCase):

    def test_empty_list(self):
        a = []
        combs = list(utils.combs_with_comp(a, 2))
        self.assertEqual(combs, [])

    def test_normal_list(self):
        a = [1, 2, 3, 4, 5]
        combs = list(utils.combs_with_comp(a, 2))
        self.assertEqual(combs, [([1, 2], [3, 4, 5]),
                                 ([1, 3], [2, 4, 5]),
                                 ([1, 4], [2, 3, 5]),
                                 ([1, 5], [2, 3, 4]),
                                 ([2, 3], [1, 4, 5]),
                                 ([2, 4], [1, 3, 5]),
                                 ([2, 5], [1, 3, 4]),
                                 ([3, 4], [1, 2, 5]),
                                 ([3, 5], [1, 2, 4]),
                                 ([4, 5], [1, 2, 3])])

    def test_string(self):
        a = 'ABCD'
        combs = list(utils.combs_with_comp(a, 2))
        self.assertEqual(combs, [(['A', 'B'], ['C', 'D']),
                                 (['A', 'C'], ['B', 'D']),
                                 (['A', 'D'], ['B', 'C']),
                                 (['B', 'C'], ['A', 'D']),
                                 (['B', 'D'], ['A', 'C']),
                                 (['C', 'D'], ['A', 'B'])])
