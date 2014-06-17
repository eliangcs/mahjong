import unittest

from mahjong.types import (GameContext, GameSettings, Hand, Player, Tile,
    TileGroup, Wall)


class TestTile(unittest.TestCase):

    def test_class_members(self):
        chars = [Tile.CHAR1, Tile.CHAR2, Tile.CHAR3, Tile.CHAR4, Tile.CHAR5,
                 Tile.CHAR6, Tile.CHAR7, Tile.CHAR8, Tile.CHAR9]
        circles = [Tile.CIRCLE1, Tile.CIRCLE2, Tile.CIRCLE3, Tile.CIRCLE4, Tile.CIRCLE5,
                   Tile.CIRCLE6, Tile.CIRCLE7, Tile.CIRCLE8, Tile.CIRCLE9]
        bamboos = [Tile.BAMBOO1, Tile.BAMBOO2, Tile.BAMBOO3, Tile.BAMBOO4, Tile.BAMBOO5,
                   Tile.BAMBOO6, Tile.BAMBOO7, Tile.BAMBOO8, Tile.BAMBOO9]
        winds = [Tile.EAST, Tile.SOUTH, Tile.WEST, Tile.NORTH]
        dragons = [Tile.RED, Tile.GREEN, Tile.WHITE]
        honors = winds + dragons
        flowers = [Tile.PLUM, Tile.ORCHID, Tile.BAMBOO, Tile.CHRYSANTH,
                   Tile.SPRING, Tile.SUMMER, Tile.AUTUMN, Tile.WINTER]

        self.assertEqual(len(Tile.ALL), 42)
        self.assertEqual(Tile.CHARS, chars)
        self.assertEqual(Tile.CIRCLES, circles)
        self.assertEqual(Tile.BAMBOOS, bamboos)
        self.assertEqual(Tile.HONORS, honors)
        self.assertEqual(Tile.FLOWERS, flowers)
        self.assertEqual(Tile.WINDS, winds)
        self.assertEqual(Tile.DRAGONS, dragons)

    def test_illegal_tile_id(self):
        with self.assertRaises(ValueError):
            Tile(0)
        with self.assertRaises(TypeError):
            Tile(None)

    def test_tile_name(self):
        self.assertEqual(Tile.CHAR5.name, 'CHAR5')
        self.assertEqual(Tile.CIRCLE5.name, 'CIRCLE5')
        self.assertEqual(Tile.BAMBOO5.name, 'BAMBOO5')
        self.assertEqual(Tile.EAST.name, 'EAST')
        self.assertEqual(Tile.RED.name, 'RED')
        self.assertEqual(Tile.PLUM.name, 'PLUM')

    def test_suit(self):
        self.assertEqual(Tile.CHAR3.suit, Tile.SUIT_CHAR)
        self.assertEqual(Tile.CIRCLE2.suit, Tile.SUIT_CIRCLE)
        self.assertEqual(Tile.BAMBOO1.suit, Tile.SUIT_BAMBOO)
        self.assertEqual(Tile.BAMBOO.suit, Tile.SUIT_FLOWER)
        self.assertEqual(Tile.SUMMER.suit, Tile.SUIT_SEASON)
        self.assertEqual(Tile.SOUTH.suit, Tile.SUIT_WIND)
        self.assertEqual(Tile.GREEN.suit, Tile.SUIT_DRAGON)

    def test_suit_name(self):
        self.assertEqual(Tile.CHAR3.suit_name, 'CHAR')
        self.assertEqual(Tile.CIRCLE2.suit_name, 'CIRCLE')
        self.assertEqual(Tile.BAMBOO1.suit_name, 'BAMBOO')
        self.assertEqual(Tile.BAMBOO.suit_name, 'FLOWER')
        self.assertEqual(Tile.SUMMER.suit_name, 'SEASON')
        self.assertEqual(Tile.SOUTH.suit_name, 'WIND')
        self.assertEqual(Tile.GREEN.suit_name, 'DRAGON')

    def test_rank(self):
        self.assertEqual(Tile.CHAR3.rank, 3)
        self.assertEqual(Tile.CHAR6.rank, 6)
        self.assertEqual(Tile.CHAR9.rank, 9)
        self.assertEqual(Tile.CIRCLE2.rank, 2)
        self.assertEqual(Tile.CIRCLE4.rank, 4)
        self.assertEqual(Tile.CIRCLE6.rank, 6)
        self.assertEqual(Tile.BAMBOO5.rank, 5)
        self.assertEqual(Tile.BAMBOO7.rank, 7)
        self.assertEqual(Tile.BAMBOO8.rank, 8)
        self.assertIsNone(Tile.BAMBOO.rank)
        self.assertIsNone(Tile.SUMMER.rank)
        self.assertIsNone(Tile.SOUTH.rank)
        self.assertIsNone(Tile.GREEN.rank)

    def test_equlity(self):
        self.assertEqual(Tile.CHAR3, Tile.CHAR3)
        self.assertEqual(Tile.CIRCLE7, Tile.CIRCLE7)
        self.assertEqual(Tile.SOUTH, Tile.SOUTH)
        self.assertNotEqual(Tile.CHAR1, Tile.CHAR2)
        self.assertNotEqual(Tile.PLUM, Tile.SUMMER)
        self.assertNotEqual(Tile.RED, Tile.GREEN)
        self.assertNotEqual(Tile.BAMBOO8, Tile.BAMBOO9)

    def test_comparator(self):
        self.assertLess(Tile.CHAR1, Tile.CHAR2)
        self.assertLess(Tile.CHAR9, Tile.CIRCLE1)
        self.assertLess(Tile.CIRCLE7, Tile.CIRCLE8)
        self.assertLess(Tile.CIRCLE9, Tile.BAMBOO1)
        self.assertLess(Tile.BAMBOO5, Tile.BAMBOO7)
        self.assertLess(Tile.BAMBOO9, Tile.EAST)
        self.assertLess(Tile.EAST, Tile.NORTH)
        self.assertLess(Tile.NORTH, Tile.RED)
        self.assertLess(Tile.WHITE, Tile.PLUM)
        self.assertLess(Tile.ORCHID, Tile.BAMBOO)
        self.assertLess(Tile.CHRYSANTH, Tile.SPRING)
        self.assertLess(Tile.SUMMER, Tile.AUTUMN)

        self.assertGreater(Tile.CHAR2, Tile.CHAR1)
        self.assertGreater(Tile.CIRCLE1, Tile.CHAR9)
        self.assertGreater(Tile.CIRCLE8, Tile.CIRCLE7)
        self.assertGreater(Tile.BAMBOO1, Tile.CIRCLE9)
        self.assertGreater(Tile.BAMBOO7, Tile.BAMBOO5)
        self.assertGreater(Tile.EAST, Tile.BAMBOO9)
        self.assertGreater(Tile.NORTH, Tile.EAST)
        self.assertGreater(Tile.RED, Tile.NORTH)
        self.assertGreater(Tile.PLUM, Tile.WHITE)
        self.assertGreater(Tile.BAMBOO, Tile.ORCHID)
        self.assertGreater(Tile.SPRING, Tile.CHRYSANTH)
        self.assertGreater(Tile.AUTUMN, Tile.SUMMER)

    def test_string_repr(self):
        self.assertEqual(str(Tile.CHAR5), 'CHAR5')
        self.assertEqual(str(Tile.CIRCLE5), 'CIRCLE5')
        self.assertEqual(str(Tile.BAMBOO5), 'BAMBOO5')
        self.assertEqual(str(Tile.EAST), 'EAST')
        self.assertEqual(str(Tile.RED), 'RED')
        self.assertEqual(str(Tile.PLUM), 'PLUM')

        self.assertEqual(repr(Tile.CHAR5), 'CHAR5')
        self.assertEqual(repr(Tile.CIRCLE5), 'CIRCLE5')
        self.assertEqual(repr(Tile.BAMBOO5), 'BAMBOO5')
        self.assertEqual(repr(Tile.EAST), 'EAST')
        self.assertEqual(repr(Tile.RED), 'RED')
        self.assertEqual(repr(Tile.PLUM), 'PLUM')

    def test_char1(self):
        tile = Tile.CHAR1
        self.assertTrue(tile.is_char())
        self.assertFalse(tile.is_circle())
        self.assertFalse(tile.is_bamboo())
        self.assertFalse(tile.is_honor())
        self.assertFalse(tile.is_wind())
        self.assertFalse(tile.is_dragon())
        self.assertFalse(tile.is_general_flower())
        self.assertFalse(tile.is_special_flower())
        self.assertFalse(tile.is_season())

    def test_circle5(self):
        tile = Tile.CIRCLE5
        self.assertFalse(tile.is_char())
        self.assertTrue(tile.is_circle())
        self.assertFalse(tile.is_bamboo())
        self.assertFalse(tile.is_honor())
        self.assertFalse(tile.is_wind())
        self.assertFalse(tile.is_dragon())
        self.assertFalse(tile.is_general_flower())
        self.assertFalse(tile.is_special_flower())
        self.assertFalse(tile.is_season())

    def test_bamboo8(self):
        tile = Tile.BAMBOO8
        self.assertFalse(tile.is_char())
        self.assertFalse(tile.is_circle())
        self.assertTrue(tile.is_bamboo())
        self.assertFalse(tile.is_honor())
        self.assertFalse(tile.is_wind())
        self.assertFalse(tile.is_dragon())
        self.assertFalse(tile.is_general_flower())
        self.assertFalse(tile.is_special_flower())
        self.assertFalse(tile.is_season())

    def test_east_wind(self):
        tile = Tile.EAST
        self.assertFalse(tile.is_char())
        self.assertFalse(tile.is_circle())
        self.assertFalse(tile.is_bamboo())
        self.assertTrue(tile.is_honor())
        self.assertTrue(tile.is_wind())
        self.assertFalse(tile.is_dragon())
        self.assertFalse(tile.is_general_flower())
        self.assertFalse(tile.is_special_flower())
        self.assertFalse(tile.is_season())

    def test_white_dragon(self):
        tile = Tile.WHITE
        self.assertFalse(tile.is_char())
        self.assertFalse(tile.is_circle())
        self.assertFalse(tile.is_bamboo())
        self.assertTrue(tile.is_honor())
        self.assertFalse(tile.is_wind())
        self.assertTrue(tile.is_dragon())
        self.assertFalse(tile.is_general_flower())
        self.assertFalse(tile.is_special_flower())
        self.assertFalse(tile.is_season())

    def test_flower_plum(self):
        tile = Tile.PLUM
        self.assertFalse(tile.is_char())
        self.assertFalse(tile.is_circle())
        self.assertFalse(tile.is_bamboo())
        self.assertFalse(tile.is_honor())
        self.assertFalse(tile.is_wind())
        self.assertFalse(tile.is_dragon())
        self.assertTrue(tile.is_general_flower())
        self.assertTrue(tile.is_special_flower())
        self.assertFalse(tile.is_season())

    def test_season_winter(self):
        tile = Tile.WINTER
        self.assertFalse(tile.is_char())
        self.assertFalse(tile.is_circle())
        self.assertFalse(tile.is_bamboo())
        self.assertFalse(tile.is_honor())
        self.assertFalse(tile.is_wind())
        self.assertFalse(tile.is_dragon())
        self.assertTrue(tile.is_general_flower())
        self.assertFalse(tile.is_special_flower())
        self.assertTrue(tile.is_season())


class TestTileGroup(unittest.TestCase):

    def test_equality(self):
        g1 = TileGroup([Tile.CHAR1, Tile.CHAR2, Tile.CHAR3], TileGroup.CHOW)
        g2 = TileGroup([Tile.CHAR1, Tile.CHAR2, Tile.CHAR3], TileGroup.CHOW)
        g3 = TileGroup([Tile.CHAR3, Tile.CHAR3, Tile.CHAR3], TileGroup.PONG)
        self.assertEqual(g1, g2)
        self.assertNotEqual(g2, g3)

    def test_string_repr(self):
        g1 = TileGroup([Tile.CHAR1, Tile.CHAR2, Tile.CHAR3], TileGroup.CHOW)
        g2 = TileGroup([Tile.CHAR3, Tile.CHAR3, Tile.CHAR3], TileGroup.PONG)
        g3 = TileGroup([Tile.EAST, Tile.EAST, Tile.EAST, Tile.EAST], TileGroup.KONG_EXPOSED)
        self.assertEqual(str(g1), 'CHOW[CHAR1, CHAR2, CHAR3]')
        self.assertEqual(str(g2), 'PONG[CHAR3, CHAR3, CHAR3]')
        self.assertEqual(str(g3), 'KONG_EXPOSED[EAST, EAST, EAST, EAST]')

    def test_iterable(self):
        group = TileGroup([Tile.CHAR1, Tile.CHAR2, Tile.CHAR3], TileGroup.CHOW)
        tiles = [tile for tile in group]
        self.assertEqual(tiles, [Tile.CHAR1, Tile.CHAR2, Tile.CHAR3])

    def test_clone(self):
        g1 = TileGroup([Tile.CHAR3, Tile.CHAR2, Tile.CHAR1], TileGroup.CHOW)
        g2 = g1.clone()
        self.assertEqual(g1, g2)

        # test if it's deep copy
        g2.tiles[0] = Tile.CHAR1
        g2.tiles[1] = Tile.CHAR1
        g2.tiles[2] = Tile.CHAR1
        g2.group_type = TileGroup.PONG
        self.assertEqual(g1.tiles, [Tile.CHAR1, Tile.CHAR2, Tile.CHAR3])
        self.assertNotEqual(g1, g2)

    def test_illegal_arguments(self):
        with self.assertRaises(ValueError):
            TileGroup([], TileGroup.CHOW)
        with self.assertRaises(ValueError):
            TileGroup([Tile.RED, Tile.RED, Tile.RED], TileGroup.CHOW - 1)


class TestHand(unittest.TestCase):

    def setUp(self):
        tiles = [Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
                 Tile.CHAR2, Tile.CHAR3, Tile.CHAR4,
                 Tile.CIRCLE4, Tile.CIRCLE4, Tile.CIRCLE5,
                 Tile.EAST, Tile.EAST, Tile.RED, Tile.WHITE]
        self.hand = Hand(tiles)

    def test_string_repr(self):
        hand = Hand([Tile.CHAR1, Tile.CHAR1, Tile.CHAR2, Tile.CHAR3])
        hand.pong(Tile.CHAR1)
        hand.add_flower(Tile.AUTUMN)
        self.assertEqual(repr(hand), '[CHAR2, CHAR3] [PONG[CHAR1, CHAR1, CHAR1]] [AUTUMN]')

        hand.last_tile = Tile.RED
        self.assertEqual(repr(hand), 'RED [CHAR2, CHAR3] [PONG[CHAR1, CHAR1, CHAR1]] [AUTUMN]')

    def test_equality(self):
        # check if it uses multiset to compare free_tiles
        tiles = [Tile.CHAR1, Tile.CHAR2, Tile.CHAR3,
                 Tile.CHAR4, Tile.CIRCLE4, Tile.CIRCLE5,
                 Tile.EAST, Tile.RED, Tile.WHITE]
        hand2 = Hand(tiles)
        self.assertNotEqual(self.hand, hand2)

        tiles = [Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
                 Tile.CHAR2, Tile.CHAR3, Tile.CHAR4,
                 Tile.CIRCLE4, Tile.CIRCLE4, Tile.CIRCLE5,
                 Tile.EAST, Tile.EAST, Tile.RED, Tile.WHITE]
        hand2 = Hand(tiles)
        self.assertEqual(self.hand, hand2)

        hand2.kong_from_other(Tile.CHAR1)
        hand2.add_flower(Tile.PLUM)
        self.assertNotEqual(self.hand, hand2)

        self.hand.add_flower(Tile.PLUM)
        self.hand.kong_from_other(Tile.CHAR1)
        self.assertEqual(self.hand, hand2)

        # check if it uses multiset to compare flowers
        self.hand.add_flower(Tile.PLUM)
        self.assertNotEqual(self.hand, hand2)

        hand2.add_flower(Tile.PLUM)
        self.hand.last_tile = Tile.RED
        self.assertNotEqual(self.hand, hand2)

        # check if last_tile is merged into free_tiles when comparing
        self.hand.remove_free_tile(Tile.RED)
        self.assertEqual(self.hand, hand2)

        # check if it uses multiset to compare fixed_groups
        self.hand.fixed_groups.append(TileGroup([Tile.CHAR1] * 4, TileGroup.KONG_EXPOSED))
        self.assertNotEqual(self.hand, hand2)

        hand2.fixed_groups.append(TileGroup([Tile.CHAR1] * 4, TileGroup.KONG_EXPOSED))
        self.assertEqual(self.hand, hand2)

    def test_clone(self):
        # clone self.hand to hand2
        self.hand.pong(Tile.EAST)
        self.hand.last_tile = Tile.WEST
        hand2 = self.hand.clone()
        self.assertEqual(self.hand, hand2)
        self.assertEqual(hand2.last_tile, Tile.WEST)

        # changes on hand2 shouldn't affect self.hand
        hand2.kong_from_other(Tile.CHAR1)
        hand2.add_flower(Tile.SPRING)
        self.assertNotEqual(self.hand, hand2)
        self.assertEqual(self.hand.last_tile, Tile.WEST)
        self.assertEqual(len(self.hand.free_tiles), 11)
        self.assertEqual(len(self.hand.flowers), 0)
        self.assertEqual(len(self.hand.fixed_groups), 1)
        self.assertEqual(len(hand2.free_tiles), 8)
        self.assertEqual(len(hand2.flowers), 1)
        self.assertEqual(len(hand2.fixed_groups), 2)

    def test_clear(self):
        empty_hand = Hand()
        self.assertEqual(empty_hand.free_tiles, [])
        self.assertEqual(empty_hand.flowers, [])
        self.assertEqual(empty_hand.fixed_groups, [])
        self.assertIsNone(empty_hand.last_tile)
        self.hand.clear()
        self.assertEqual(self.hand, empty_hand)

    def test_move_last_tile(self):
        # move_last_tile() does nothing when last_tile is None
        hand2 = self.hand.clone()
        self.hand.move_last_tile()
        self.assertEqual(self.hand, hand2)

        self.hand.last_tile = Tile.GREEN
        self.hand.move_last_tile()
        hand2.add_free_tile(Tile.GREEN)
        self.assertEqual(self.hand.free_tiles, hand2.free_tiles)
        self.assertEqual(self.hand.fixed_groups, [])
        self.assertEqual(self.hand.flowers, [])
        self.assertIsNone(self.hand.last_tile)

    def test_remove_last_tile(self):
        # remove_last_tile() does nothing when last_tile is None
        hand2 = self.hand.clone()
        self.assertIsNone(self.hand.remove_last_tile())
        self.assertEqual(self.hand, hand2)

        self.hand.last_tile = Tile.GREEN
        self.assertNotEqual(self.hand, hand2)

        self.assertEqual(self.hand.remove_last_tile(), Tile.GREEN)
        self.assertEqual(self.hand, hand2)
        self.assertIsNone(self.hand.last_tile)

    def test_add_free_tiles(self):
        hand = Hand()
        hand.add_free_tile(Tile.RED)
        hand.add_free_tile(Tile.CHAR3)
        hand.add_free_tile(Tile.CIRCLE7)
        self.assertEqual(hand.free_tiles, [Tile.CHAR3, Tile.CIRCLE7, Tile.RED])
        self.assertEqual(hand.fixed_groups, [])
        self.assertEqual(hand.flowers, [])
        self.assertIsNone(hand.last_tile)

        more_tiles = [Tile.BAMBOO1, Tile.BAMBOO2, Tile.CIRCLE8]
        hand.add_free_tiles(more_tiles)
        self.assertEqual(hand.free_tiles, [Tile.CHAR3, Tile.CIRCLE7, Tile.CIRCLE8,
                                           Tile.BAMBOO1, Tile.BAMBOO2, Tile.RED])
        self.assertEqual(hand.fixed_groups, [])
        self.assertEqual(hand.flowers, [])
        self.assertIsNone(hand.last_tile)

    def test_remove_free_tile(self):
        self.hand.remove_free_tile(Tile.CHAR4)
        self.hand.remove_free_tile(Tile.WHITE)
        self.hand.remove_free_tile(Tile.RED)
        self.hand.remove_free_tile(Tile.EAST)
        self.assertEqual(self.hand.free_tiles,
                         [Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
                          Tile.CHAR2, Tile.CHAR3, Tile.CIRCLE4,
                          Tile.CIRCLE4, Tile.CIRCLE5, Tile.EAST])
        self.assertEqual(self.hand.fixed_groups, [])
        self.assertEqual(self.hand.flowers, [])
        self.assertIsNone(self.hand.last_tile)

        with self.assertRaises(ValueError):
            self.hand.remove_free_tile(Tile.GREEN)

    def test_count(self):
        self.hand.last_tile = Tile.CHAR1
        self.hand.fixed_groups = [
            TileGroup([Tile.CIRCLE4, Tile.CIRCLE5, Tile.CIRCLE6], TileGroup.CHOW),
            TileGroup([Tile.CHAR2] * 3, TileGroup.PONG)
        ]
        self.assertEqual(self.hand.count(Tile.CHAR1), 4)
        self.assertEqual(self.hand.count(Tile.CHAR1, last_tile=False), 3)
        self.assertEqual(self.hand.count(Tile.CHAR1, free_tiles=False), 1)
        self.assertEqual(self.hand.count(Tile.CHAR2), 1)
        self.assertEqual(self.hand.count(Tile.CHAR2, free_tiles=False), 0)
        self.assertEqual(self.hand.count(Tile.CHAR2, fixed_groups=True), 4)
        self.assertEqual(self.hand.count(Tile.CIRCLE4), 2)
        self.assertEqual(self.hand.count(Tile.CIRCLE4, fixed_groups=True), 3)

    def test_contains(self):
        self.hand.last_tile = Tile.SOUTH
        self.hand.fixed_groups = [
            TileGroup([Tile.BAMBOO1, Tile.BAMBOO2, Tile.BAMBOO3], TileGroup.CHOW),
            TileGroup([Tile.WEST] * 3, TileGroup.PONG)
        ]
        self.assertTrue(self.hand.contains(Tile.CHAR1))
        self.assertTrue(self.hand.contains(Tile.CHAR3))
        self.assertFalse(self.hand.contains(Tile.CHAR5))
        self.assertFalse(self.hand.contains(Tile.CHAR1, free_tiles=False))
        self.assertFalse(self.hand.contains(Tile.CHAR3, free_tiles=False))

        self.assertTrue(self.hand.contains(Tile.SOUTH))
        self.assertFalse(self.hand.contains(Tile.SOUTH, last_tile=False))

        self.assertFalse(self.hand.contains(Tile.BAMBOO3))
        self.assertTrue(self.hand.contains(Tile.BAMBOO3, fixed_groups=True))
        self.assertTrue(self.hand.contains(Tile.BAMBOO3, free_tiles=False, last_tile=False, fixed_groups=True))

        self.assertFalse(self.hand.contains(Tile.WEST))
        self.assertTrue(self.hand.contains(Tile.WEST, fixed_groups=True))

    def test_add_flower(self):
        self.hand.add_flower(Tile.PLUM)
        self.hand.add_flower(Tile.WINTER)
        self.hand.add_flower(Tile.ORCHID)
        self.assertEqual(self.hand.flowers, [Tile.PLUM, Tile.WINTER, Tile.ORCHID])
        self.assertEqual(self.hand.free_tiles,
                         [Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
                          Tile.CHAR2, Tile.CHAR3, Tile.CHAR4,
                          Tile.CIRCLE4, Tile.CIRCLE4, Tile.CIRCLE5,
                          Tile.EAST, Tile.EAST, Tile.RED, Tile.WHITE])
        self.assertEqual(self.hand.fixed_groups, [])
        self.assertIsNone(self.hand.last_tile)

    def test_move_flowers(self):
        self.hand.add_free_tile(Tile.PLUM)
        self.hand.add_free_tile(Tile.WINTER)
        self.hand.add_free_tile(Tile.ORCHID)
        self.hand.last_tile = Tile.SUMMER
        self.hand.move_flowers()
        self.assertEqual(self.hand.flowers, [Tile.PLUM, Tile.ORCHID, Tile.WINTER, Tile.SUMMER])
        self.assertEqual(self.hand.free_tiles,
                         [Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
                          Tile.CHAR2, Tile.CHAR3, Tile.CHAR4,
                          Tile.CIRCLE4, Tile.CIRCLE4, Tile.CIRCLE5,
                          Tile.EAST, Tile.EAST, Tile.RED, Tile.WHITE])
        self.assertEqual(self.hand.fixed_groups, [])
        self.assertIsNone(self.hand.last_tile)

    def test_discard(self):
        self.hand.last_tile = Tile.GREEN
        self.hand.discard(Tile.GREEN)
        self.assertIsNone(self.hand.last_tile)
        self.assertEqual(self.hand.free_tiles,
                         [Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
                          Tile.CHAR2, Tile.CHAR3, Tile.CHAR4,
                          Tile.CIRCLE4, Tile.CIRCLE4, Tile.CIRCLE5,
                          Tile.EAST, Tile.EAST, Tile.RED, Tile.WHITE])

        self.hand.last_tile = Tile.CHAR5
        self.hand.discard(Tile.WHITE)
        self.assertIsNone(self.hand.last_tile)
        self.assertEqual(self.hand.free_tiles,
                         [Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
                          Tile.CHAR2, Tile.CHAR3, Tile.CHAR4,
                          Tile.CHAR5, Tile.CIRCLE4, Tile.CIRCLE4,
                          Tile.CIRCLE5, Tile.EAST, Tile.EAST, Tile.RED])

        with self.assertRaises(ValueError):
            self.hand.discard(Tile.WEST)

        self.assertIsNone(self.hand.last_tile)
        self.assertEqual(self.hand.free_tiles,
                         [Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
                          Tile.CHAR2, Tile.CHAR3, Tile.CHAR4,
                          Tile.CHAR5, Tile.CIRCLE4, Tile.CIRCLE4,
                          Tile.CIRCLE5, Tile.EAST, Tile.EAST, Tile.RED])

    def test_num_kongs(self):
        self.assertEqual(self.hand.num_kongs(), 0)

        self.hand.kong_from_other(Tile.CHAR1)
        self.hand.pong(Tile.EAST)
        self.assertEqual(self.hand.num_kongs(), 1)

        group = TileGroup([Tile.RED] * 4, TileGroup.KONG_CONCEALED)
        self.hand.fixed_groups.append(group)
        self.hand.fixed_groups.append(group)
        self.hand.chow([Tile.CHAR3, Tile.CHAR4], Tile.CHAR5)
        self.assertEqual(self.hand.num_kongs(), 3)

        self.assertEqual(self.hand.num_kongs(concealed=False), 1)
        self.assertEqual(self.hand.num_kongs(exposed=False), 2)
        self.assertEqual(self.hand.num_kongs(exposed=False, concealed=False), 0)

    def test_num_pongs(self):
        self.assertEqual(self.hand.num_pongs(), 0)

        self.hand.pong(Tile.CHAR1)
        self.hand.pong(Tile.EAST)
        self.assertEqual(self.hand.num_pongs(), 2)

        group = TileGroup([Tile.RED] * 4, TileGroup.KONG_CONCEALED)
        self.hand.fixed_groups.append(group)
        self.hand.chow([Tile.CHAR3, Tile.CHAR4], Tile.CHAR5)
        self.assertEqual(self.hand.num_pongs(), 2)

        self.hand.pong(Tile.CIRCLE4)
        self.assertEqual(self.hand.num_pongs(), 3)

    def test_num_chows(self):
        self.assertEqual(self.hand.num_chows(), 0)

        self.hand.pong(Tile.EAST)
        group = TileGroup([Tile.WHITE] * 4, TileGroup.KONG_CONCEALED)
        self.hand.fixed_groups.append(group)
        self.assertEqual(self.hand.num_chows(), 0)

        self.hand.chow([Tile.CHAR1, Tile.CHAR2], Tile.CHAR3)
        self.hand.chow([Tile.CHAR3, Tile.CHAR4], Tile.CHAR5)
        self.assertEqual(self.hand.num_chows(), 2)

    def test_chow(self):
        group = self.hand.chow([Tile.CHAR3, Tile.CHAR4], Tile.CHAR5)
        self.assertEqual(self.hand.free_tiles,
                         [Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
                          Tile.CHAR2, Tile.CIRCLE4, Tile.CIRCLE4,
                          Tile.CIRCLE5, Tile.EAST, Tile.EAST,
                          Tile.RED, Tile.WHITE])
        self.assertEqual(group, TileGroup([Tile.CHAR3, Tile.CHAR4, Tile.CHAR5], TileGroup.CHOW))
        self.assertEqual(self.hand.fixed_groups, [group])
        self.assertEqual(self.hand.flowers, [])
        self.assertIsNone(self.hand.last_tile)

    def test_pong(self):
        group1 = self.hand.pong(Tile.CHAR1)
        group2 = self.hand.pong(Tile.CIRCLE4)
        self.assertEqual(self.hand.free_tiles,
                         [Tile.CHAR1, Tile.CHAR2, Tile.CHAR3,
                          Tile.CHAR4, Tile.CIRCLE5, Tile.EAST,
                          Tile.EAST, Tile.RED, Tile.WHITE])
        self.assertEqual(group1, TileGroup([Tile.CHAR1] * 3, TileGroup.PONG))
        self.assertEqual(group2, TileGroup([Tile.CIRCLE4] * 3, TileGroup.PONG))
        self.assertEqual(self.hand.fixed_groups, [group1, group2])
        self.assertEqual(self.hand.flowers, [])
        self.assertIsNone(self.hand.last_tile)

    def test_kong_from_other(self):
        group = self.hand.kong_from_other(Tile.CHAR1)
        self.assertEqual(self.hand.free_tiles,
                         [Tile.CHAR2, Tile.CHAR3, Tile.CHAR4,
                          Tile.CIRCLE4, Tile.CIRCLE4, Tile.CIRCLE5,
                          Tile.EAST, Tile.EAST, Tile.RED, Tile.WHITE])
        self.assertEqual(group, TileGroup([Tile.CHAR1] * 4, TileGroup.KONG_EXPOSED))
        self.assertEqual(self.hand.fixed_groups, [group])
        self.assertEqual(self.hand.flowers, [])
        self.assertIsNone(self.hand.last_tile)

    def test_appended_kong_from_self(self):
        self.hand.pong(Tile.EAST)
        self.hand.last_tile = Tile.EAST
        group = self.hand.kong_from_self()
        self.assertEqual(self.hand.free_tiles,
                         [Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
                          Tile.CHAR2, Tile.CHAR3, Tile.CHAR4,
                          Tile.CIRCLE4, Tile.CIRCLE4, Tile.CIRCLE5,
                          Tile.RED, Tile.WHITE])
        self.assertEqual(group, TileGroup([Tile.EAST] * 4, TileGroup.KONG_EXPOSED))
        self.assertEqual(self.hand.fixed_groups, [group])
        self.assertEqual(self.hand.flowers, [])
        self.assertIsNone(self.hand.last_tile)

    def test_concealed_kong_from_self(self):
        self.hand.last_tile = Tile.CHAR1
        group = self.hand.kong_from_self()
        self.assertEqual(self.hand.free_tiles,
                         [Tile.CHAR2, Tile.CHAR3, Tile.CHAR4,
                          Tile.CIRCLE4, Tile.CIRCLE4, Tile.CIRCLE5,
                          Tile.EAST, Tile.EAST, Tile.RED, Tile.WHITE])
        self.assertEqual(group, TileGroup([Tile.CHAR1] * 4, TileGroup.KONG_CONCEALED))
        self.assertEqual(self.hand.fixed_groups, [group])
        self.assertEqual(self.hand.flowers, [])
        self.assertIsNone(self.hand.last_tile)

    def test_get_chow_combs(self):
        self.assertEqual(self.hand.get_chow_combs(Tile.CIRCLE3), [(Tile.CIRCLE4, Tile.CIRCLE5)])
        self.assertEqual(self.hand.get_chow_combs(Tile.CHAR3), [(Tile.CHAR1, Tile.CHAR2), (Tile.CHAR2, Tile.CHAR4)])
        self.assertEqual(self.hand.get_chow_combs(Tile.CHAR2), [(Tile.CHAR1, Tile.CHAR3), (Tile.CHAR3, Tile.CHAR4)])
        self.assertEqual(self.hand.get_chow_combs(Tile.CHAR9), [])
        self.assertEqual(self.hand.get_chow_combs(Tile.RED), [])

    def test_can_chow(self):
        self.assertTrue(self.hand.can_chow(Tile.CIRCLE3))
        self.assertTrue(self.hand.can_chow(Tile.CHAR3))
        self.assertTrue(self.hand.can_chow(Tile.CHAR2))
        self.assertFalse(self.hand.can_chow(Tile.CHAR9))
        self.assertFalse(self.hand.can_chow(Tile.RED))

    def test_can_pong(self):
        self.assertTrue(self.hand.can_pong(Tile.CHAR1))
        self.assertTrue(self.hand.can_pong(Tile.CIRCLE4))
        self.assertTrue(self.hand.can_pong(Tile.EAST))
        self.assertFalse(self.hand.can_pong(Tile.CHAR3))
        self.assertFalse(self.hand.can_pong(Tile.RED))
        self.assertFalse(self.hand.can_pong(Tile.GREEN))

    def test_can_kong(self):
        self.assertTrue(self.hand.can_kong(Tile.CHAR1))
        self.assertFalse(self.hand.can_kong(Tile.CHAR2))
        self.assertFalse(self.hand.can_kong(Tile.CHAR3))
        self.assertFalse(self.hand.can_kong(Tile.EAST))
        self.assertFalse(self.hand.can_kong(Tile.WHITE))

    def test_can_self_kong(self):
        self.assertFalse(self.hand.can_self_kong())

        self.hand.last_tile = Tile.CHAR1
        self.assertTrue(self.hand.can_self_kong())

        self.hand.last_tile = Tile.EAST
        self.assertFalse(self.hand.can_self_kong())

        self.hand.pong(Tile.EAST)
        self.assertTrue(self.hand.can_self_kong())

        self.hand.pong(Tile.CIRCLE4)
        self.assertTrue(self.hand.can_self_kong())

    def test_can_appended_kong(self):
        self.assertFalse(self.hand.can_appended_kong())

        self.hand.pong(Tile.EAST)
        self.hand.pong(Tile.CIRCLE4)
        self.assertFalse(self.hand.can_appended_kong())

        self.hand.last_tile = Tile.EAST
        self.assertTrue(self.hand.can_appended_kong())

        self.hand.last_tile = Tile.WHITE
        self.assertFalse(self.hand.can_appended_kong())

        self.hand.last_tile = Tile.CIRCLE4
        self.assertTrue(self.hand.can_appended_kong())

        self.hand.last_tile = None
        self.assertFalse(self.hand.can_appended_kong())

    def test_can_concealed_kong(self):
        self.assertFalse(self.hand.can_concealed_kong())

        self.hand.last_tile = Tile.CHAR1
        self.assertTrue(self.hand.can_concealed_kong())

        self.hand.last_tile = Tile.CIRCLE4
        self.assertFalse(self.hand.can_concealed_kong())

        self.hand.add_free_tile(Tile.CIRCLE4)
        self.hand.remove_free_tile(Tile.RED)
        self.assertTrue(self.hand.can_concealed_kong())

    def test_can_win(self):
        hand = Hand([Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
                     Tile.CIRCLE7, Tile.CIRCLE8, Tile.CIRCLE9,
                     Tile.RED, Tile.RED, Tile.RED,
                     Tile.WEST, Tile.WEST, Tile.WEST, Tile.BAMBOO5])
        self.assertTrue(hand.can_win(Tile.BAMBOO5))
        self.assertFalse(hand.can_win(Tile.BAMBOO6))
        self.assertFalse(hand.can_win(Tile.EAST))
        self.assertFalse(hand.can_win(Tile.RED))
        self.assertIsNone(hand.last_tile)

        hand = Hand([Tile.BAMBOO1,
                     Tile.CIRCLE4, Tile.CIRCLE4, Tile.CIRCLE4,
                     Tile.BAMBOO5, Tile.BAMBOO5, Tile.BAMBOO5,
                     Tile.BAMBOO7, Tile.BAMBOO7, Tile.BAMBOO7,
                     Tile.CIRCLE8, Tile.CIRCLE8, Tile.CIRCLE8])
        self.assertTrue(hand.can_win(Tile.BAMBOO1))
        self.assertFalse(hand.can_win())
        self.assertFalse(hand.can_win(Tile.BAMBOO2))
        self.assertFalse(hand.can_win(Tile.GREEN))
        self.assertIsNone(hand.last_tile)

        self.assertTrue(hand.ready())
        self.assertEqual(hand.waiting_tiles(), [Tile.BAMBOO1])

        hand = Hand([Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
                     Tile.CHAR9, Tile.CHAR9,
                     Tile.BAMBOO1, Tile.BAMBOO1,
                     Tile.WHITE, Tile.WHITE, Tile.WHITE,
                     Tile.WEST, Tile.WEST, Tile.WEST])
        hand.last_tile = Tile.CHAR9
        self.assertTrue(hand.can_win())
        hand.last_tile = Tile.CHAR1
        self.assertFalse(hand.can_win())
        hand.last_tile = Tile.BAMBOO1
        self.assertTrue(hand.can_win())
        hand.last_tile = Tile.GREEN
        self.assertFalse(hand.can_win())
        self.assertEqual(hand.last_tile, Tile.GREEN)

        self.assertTrue(hand.ready())
        self.assertEqual(hand.waiting_tiles(), [Tile.CHAR9, Tile.BAMBOO1])

        hand = Hand([Tile.GREEN])
        self.assertTrue(hand.can_win(Tile.GREEN))
        self.assertFalse(hand.can_win(Tile.RED))
        self.assertFalse(hand.can_win(Tile.WHITE))
        self.assertIsNone(hand.last_tile)

        self.assertTrue(hand.ready())
        self.assertEqual(hand.waiting_tiles(), [Tile.GREEN])

        hand = Hand([Tile.RED, Tile.RED, Tile.RED,
                     Tile.GREEN, Tile.GREEN, Tile.GREEN,
                     Tile.SOUTH, Tile.SOUTH, Tile.SOUTH,
                     Tile.BAMBOO1, Tile.BAMBOO2, Tile.BAMBOO3,
                     Tile.CHAR9, Tile.CHAR9,
                     Tile.CHAR4, Tile.CHAR5])
        self.assertTrue(hand.can_win(Tile.CHAR3))
        self.assertTrue(hand.can_win(Tile.CHAR6))
        self.assertFalse(hand.can_win(Tile.CHAR9))
        self.assertFalse(hand.can_win(Tile.RED))
        self.assertIsNone(hand.last_tile)

        self.assertTrue(hand.ready())
        self.assertEqual(hand.waiting_tiles(), [Tile.CHAR3, Tile.CHAR6])

        hand = Hand([Tile.CHAR2, Tile.CHAR2,
                     Tile.CHAR3, Tile.CHAR4, Tile.CHAR5,
                     Tile.CHAR6, Tile.CHAR7])
        self.assertTrue(hand.can_win(Tile.CHAR2))
        self.assertTrue(hand.can_win(Tile.CHAR5))
        self.assertTrue(hand.can_win(Tile.CHAR8))
        self.assertFalse(hand.can_win(Tile.CHAR1))
        self.assertFalse(hand.can_win(Tile.CHAR3))
        self.assertFalse(hand.can_win(Tile.CHAR4))
        self.assertIsNone(hand.last_tile)

        self.assertTrue(hand.ready())
        self.assertEqual(hand.waiting_tiles(), [Tile.CHAR2, Tile.CHAR5, Tile.CHAR8])

        # a unready hand
        hand = Hand([Tile.RED, Tile.WHITE, Tile.RED,
                     Tile.GREEN, Tile.EAST, Tile.GREEN,
                     Tile.SOUTH, Tile.SOUTH, Tile.SOUTH,
                     Tile.BAMBOO1, Tile.BAMBOO2, Tile.BAMBOO3,
                     Tile.CHAR9, Tile.CHAR3,
                     Tile.CHAR4, Tile.CIRCLE1])
        self.assertFalse(hand.can_win(Tile.CHAR1))
        self.assertFalse(hand.can_win(Tile.CHAR5))
        self.assertFalse(hand.can_win(Tile.CIRCLE3))
        self.assertFalse(hand.can_win(Tile.CIRCLE8))
        self.assertFalse(hand.can_win(Tile.BAMBOO4))
        self.assertFalse(hand.can_win(Tile.BAMBOO9))
        self.assertFalse(hand.can_win(Tile.GREEN))
        self.assertFalse(hand.can_win(Tile.NORTH))
        self.assertIsNone(hand.last_tile)

        self.assertFalse(hand.ready())
        self.assertFalse(hand.waiting_tiles())

    def test_illegal_chow(self):
        with self.assertRaises(ValueError):
            self.hand.chow([Tile.BAMBOO1, Tile.BAMBOO2], Tile.BAMBOO3)

    def test_illegal_pong(self):
        with self.assertRaises(ValueError):
            self.hand.pong(Tile.BAMBOO1)

    def test_illegal_kong(self):
        with self.assertRaises(ValueError):
            self.hand.kong_from_other(Tile.BAMBOO1)
        with self.assertRaises(ValueError):
            self.hand.last_tile = None
            self.hand.kong_from_self()
        with self.assertRaises(ValueError):
            self.hand.last_tile = Tile.CHAR2
            self.hand.kong_from_self()


class TestWall(unittest.TestCase):

    def test_creation(self):
        w1 = Wall()
        w2 = Wall(flowers=False)
        w3 = Wall(honors=False, flowers=False)
        self.assertEqual(w1.num_tiles(), 144)
        self.assertEqual(w2.num_tiles(), 136)
        self.assertEqual(w3.num_tiles(), 108)

    def test_equality(self):
        w1 = Wall()
        w2 = Wall()
        self.assertEqual(w1, w2)

        w2.draw()
        self.assertNotEqual(w1, w2)

    def test_iterable(self):
        wall = Wall(bamboos=False)
        tiles = [tile for tile in wall]
        self.assertEqual(len(tiles), 108)

        num_chars = len(filter(lambda x: x.is_char(), tiles))
        num_bamboos = len(filter(lambda x: x.is_bamboo(), tiles))
        num_whites = len(filter(lambda x: x == Tile.WHITE, tiles))
        num_wests = len(filter(lambda x: x == Tile.WEST, tiles))
        num_summers = len(filter(lambda x: x == Tile.SUMMER, tiles))
        self.assertEqual(num_chars, 36)
        self.assertEqual(num_bamboos, 0)
        self.assertEqual(num_whites, 4)
        self.assertEqual(num_wests, 4)
        self.assertEqual(num_summers, 1)

    def test_clone(self):
        w1 = Wall()
        w2 = w1.clone()
        self.assertEqual(w1, w2)

        w2.draw()
        self.assertNotEqual(w1, w2)
        self.assertEqual(w2.num_tiles(), 143)

        w1.draw()
        self.assertEqual(w1, w2)

    def test_shuffle(self):
        w1 = Wall()
        w2 = Wall()
        self.assertEqual(w1, w2)

        w2.shuffle()
        tiles1 = [tile for tile in w1]
        tiles2 = [tile for tile in w2]
        self.assertNotEqual(tiles1[0:5], tiles2[0:5])

    def test_draw(self):
        wall = Wall()
        tiles = []
        while True:
            tile = wall.draw()
            if not tile:
                break
            tiles.append(tile)
        self.assertEqual(wall.num_tiles(), 0)
        self.assertEqual(len(tiles), 144)

        num_chars = len(filter(lambda x: x.is_char(), tiles))
        num_whites = len(filter(lambda x: x == Tile.WHITE, tiles))
        num_summers = len(filter(lambda x: x == Tile.SUMMER, tiles))
        self.assertEqual(num_chars, 36)
        self.assertEqual(num_whites, 4)
        self.assertEqual(num_summers, 1)


class TestGameSettings(unittest.TestCase):

    def test_default_values(self):
        gs = GameSettings()
        self.assertEqual(gs.num_hand_tiles, 16)
        self.assertEqual(gs.max_dealer_defended, 999)

    def test_equlity(self):
        gs1 = GameSettings()
        gs2 = GameSettings()
        self.assertEqual(gs1, gs2)

        gs1.num_hand_tiles = 16
        self.assertNotEqual(gs1, gs2)

        gs2.num_hand_tiles = 16
        self.assertEqual(gs1, gs2)

    def test_attr_accessors(self):
        gs = GameSettings()
        gs.num_hand_tiles = 16
        gs.max_dealer_defended = 9
        self.assertEqual(gs.num_hand_tiles, 16)
        self.assertEqual(gs.max_dealer_defended, 9)

        with self.assertRaises(AttributeError):
            value = gs.illegal_attr_name
            print value

        with self.assertRaises(AttributeError):
            gs.illegal_attr_name = None

    def test_total_tiles(self):
        gs = GameSettings()
        self.assertEqual(gs.total_tiles(), 144)

        gs.wall_honors = False
        gs.wall_flowers = False
        self.assertEqual(gs.total_tiles(), 108)

        gs.wall_bamboos = False
        gs.wall_chars = False
        gs.wall_circles = False
        self.assertEqual(gs.total_tiles(), 0)


class TestPlayer(unittest.TestCase):

    def test_equality(self):
        p1 = Player()
        p2 = Player()
        self.assertEqual(p1, p2)

        p1.hand.add_flower(Tile.SUMMER)
        self.assertNotEqual(p1, p2)
        p2.hand.add_flower(Tile.SUMMER)
        self.assertEqual(p1, p2)

        p1.decision = 'hello'
        self.assertNotEqual(p1, p2)
        p2.decision = 'hello'
        self.assertEqual(p1, p2)

        p1.discarded.append(Tile.CHAR1)
        self.assertNotEqual(p1, p2)
        p2.discarded.append(Tile.CHAR1)
        self.assertEqual(p1, p2)

        p1.extra['hello'] = True
        self.assertNotEqual(p1, p2)
        p2.extra['hello'] = True
        self.assertEqual(p1, p2)

        # different types
        self.assertNotEqual(p1, None)
        self.assertNotEqual(p1, Hand())

    def test_reset(self):
        p = Player()
        p.hand.add_free_tile(Tile.CHAR1)
        p.discarded.append(Tile.CHAR2)
        p.decision = 'hello'
        p.extra['hello'] = True
        p.reset()
        self.assertEqual(p.hand, Hand())
        self.assertEqual(p.discarded, [])
        self.assertIsNone(p.decision)
        self.assertEqual(p.extra, {})

    def test_clone(self):
        p1 = Player()
        p1.hand.add_free_tile(Tile.CHAR1)
        p1.discarded.append(Tile.CHAR2)
        p1.decision = 'hello'
        p1.extra['hello'] = True
        p2 = p1.clone()
        self.assertEqual(p1, p2)

        # modifying p1 doesn't affect p2
        p1.hand.add_free_tile(Tile.CHAR1)
        p1.discarded.append(Tile.CHAR2)
        p1.decision = 'world'
        p1.extra['hello'] = False
        self.assertEqual(p2.hand, Hand([Tile.CHAR1]))
        self.assertEqual(p2.discarded, [Tile.CHAR2])
        self.assertEqual(p2.decision, 'hello')
        self.assertEqual(p2.extra, { 'hello': True })

    def test_discard(self):
        p = Player()
        p.hand.add_free_tiles([Tile.CHAR1, Tile.EAST, Tile.WEST])
        p.hand.last_tile = Tile.WEST
        p.discard(Tile.WEST)
        self.assertEqual(p.hand.free_tiles, [Tile.CHAR1, Tile.EAST, Tile.WEST])
        self.assertIsNone(p.hand.last_tile)
        self.assertEqual(p.discarded, [Tile.WEST])

        p.discard(Tile.CHAR1)
        self.assertEqual(p.hand.free_tiles, [Tile.EAST, Tile.WEST])
        self.assertIsNone(p.hand.last_tile)
        self.assertEqual(p.discarded, [Tile.WEST, Tile.CHAR1])

        p.hand.last_tile = Tile.SOUTH
        with self.assertRaises(ValueError):
            p.hand.discard(Tile.NORTH)
        self.assertEqual(p.hand.free_tiles, [Tile.EAST, Tile.WEST])
        self.assertEqual(p.hand.last_tile, Tile.SOUTH)
        self.assertEqual(p.discarded, [Tile.WEST, Tile.CHAR1])

        p.discard()
        self.assertEqual(p.hand.free_tiles, [Tile.EAST, Tile.WEST])
        self.assertIsNone(p.hand.last_tile)
        self.assertEqual(p.discarded, [Tile.WEST, Tile.CHAR1, Tile.SOUTH])

        with self.assertRaises(ValueError):
            p.discard()


class TestGameContext(unittest.TestCase):

    def test_equality(self):
        c = GameContext()
        self.assertEqual(c, GameContext())

        c = GameContext()
        c.state = 'wall-built'
        self.assertNotEqual(c, GameContext())

        c = GameContext()
        c.players[0].hand.add_free_tile(Tile.RED)
        self.assertNotEqual(c, GameContext())

        c = GameContext()
        c.players[0].discarded.append(Tile.RED)
        self.assertNotEqual(c, GameContext())

        c = GameContext()
        c.last_discarded = Tile.RED
        self.assertNotEqual(c, GameContext())

        c = GameContext()
        c.cur_player_idx = 1
        self.assertNotEqual(c, GameContext())

        c = GameContext()
        c.last_player_idx = 1
        self.assertNotEqual(c, GameContext())

        c = GameContext()
        c.round = 1
        self.assertNotEqual(c, GameContext())

        c = GameContext()
        c.match = 1
        self.assertNotEqual(c, GameContext())

        c = GameContext()
        c.dealer = 1
        self.assertNotEqual(c, GameContext())

        c = GameContext()
        c.dealer_defended = 1
        self.assertNotEqual(c, GameContext())

        c = GameContext()
        c.player_decision = 'test'
        self.assertNotEqual(c, GameContext())

    def test_reset(self):
        c1 = GameContext()
        c2 = GameContext()
        self.assertEqual(c1, c2)

        c1.state = 'dealt'
        c1.wall = Wall()
        self.assertNotEqual(c1, c2)

        c1.reset()
        self.assertEqual(c1, c2)

    def test_clone(self):
        c1 = GameContext()
        c1.wall = Wall()
        c2 = c1.clone()
        self.assertEqual(c1, c2)

        c2.wall.draw()
        self.assertNotEqual(c1, c2)

        c1.wall.draw()
        self.assertEqual(c1, c2)

        c2.players[0].hand.add_free_tile(Tile.RED)
        self.assertNotEqual(c1, c2)

        c1.players[0].hand.add_free_tile(Tile.RED)
        self.assertEqual(c1, c2)

        c2.players[0].discarded.append(Tile.RED)
        self.assertNotEqual(c1, c2)

        c1.players[0].discarded.append(Tile.RED)
        self.assertEqual(c1, c2)

    def test_player(self):
        c = GameContext()
        c.players[0].hand.add_free_tile(Tile.SPRING)
        c.players[1].hand.add_free_tile(Tile.SUMMER)
        c.players[2].hand.add_free_tile(Tile.AUTUMN)
        c.players[3].hand.add_free_tile(Tile.WINTER)
        c.cur_player_idx = 3
        self.assertEqual(c.player().hand.free_tiles, [Tile.WINTER])
        self.assertEqual(c.player(1).hand.free_tiles, [Tile.SPRING])
        self.assertEqual(c.player(2).hand.free_tiles, [Tile.SUMMER])
        self.assertEqual(c.player(-1).hand.free_tiles, [Tile.AUTUMN])

        c.cur_player_idx = None
        self.assertIsNone(c.player())

    def test_reset_players(self):
        empty_player = Player()
        c = GameContext()
        c.players[0].hand.add_free_tile(Tile.SPRING)
        c.players[1].hand.add_free_tile(Tile.SUMMER)
        c.players[2].hand.add_free_tile(Tile.AUTUMN)
        c.players[3].hand.add_free_tile(Tile.WINTER)
        c.cur_player_idx = 3
        c.reset_players()
        self.assertEqual(c.players[0], empty_player)
        self.assertEqual(c.players[1], empty_player)
        self.assertEqual(c.players[2], empty_player)
        self.assertEqual(c.players[3], empty_player)
        self.assertEqual(c.cur_player_idx, 3)

    def test_is_tie(self):
        gs = GameSettings()
        gs.tie_on_4_kongs = True
        gs.tie_on_4_waiting = True
        gs.tie_on_winds = 'west'
        gs.tie_wall = 16
        gs.tie_wall_per_kong = 1

        c = GameContext(settings=gs)
        c.wall = Wall()
        self.assertFalse(c.is_tie())

        c.state = 'end'
        c.winners = None
        self.assertTrue(c.is_tie())

        c.state = 'start'
        c.players[0].extra['declared_ready'] = True
        c.players[1].extra['declared_ready'] = True
        c.players[2].extra['declared_ready'] = True
        c.players[3].extra['declared_ready'] = True
        self.assertTrue(c.is_tie())

        c.players[0].extra['declared_ready'] = False
        self.assertFalse(c.is_tie())

        c.players[0].hand.fixed_groups.append(TileGroup([Tile.RED] * 4, TileGroup.KONG_EXPOSED))
        c.players[2].hand.fixed_groups.append(TileGroup([Tile.GREEN] * 4, TileGroup.KONG_EXPOSED))
        c.players[3].hand.fixed_groups.append(TileGroup([Tile.WHITE] * 4, TileGroup.KONG_CONCEALED))
        while c.wall.num_tiles() > 20:
            c.wall.draw()
        self.assertFalse(c.is_tie())

        # wall tie
        c.wall.draw()
        self.assertEqual(c.wall.num_tiles(), 19)
        self.assertTrue(c.is_tie())
        self.assertFalse(c.is_tie(wall_tie=False))

        # four kong tie
        c.wall.tiles.append(Tile.CHAR1)
        c.wall.tiles.append(Tile.CHAR1)
        self.assertFalse(c.is_tie())
        c.players[3].hand.fixed_groups.append(TileGroup([Tile.SOUTH] * 4, TileGroup.KONG_CONCEALED))
        self.assertTrue(c.is_tie())
        self.assertFalse(c.is_tie(four_kongs=False))

        c = GameContext(settings=gs)
        c.wall = Wall()

        # four wind tie
        c.players[0].discarded.append(Tile.WEST)
        c.players[1].discarded.append(Tile.WEST)
        c.players[2].discarded.append(Tile.WEST)
        c.players[3].discarded.append(Tile.WEST)
        self.assertTrue(c.is_tie())
        self.assertFalse(c.is_tie(four_winds=False))

        c.players[3].discarded[0] = Tile.EAST
        self.assertFalse(c.is_tie())

        gs.tie_on_winds = 'all'
        self.assertFalse(c.is_tie())

        c.players[0].discarded[0] = Tile.EAST
        c.players[1].discarded[0] = Tile.EAST
        c.players[2].discarded[0] = Tile.EAST
        self.assertTrue(c.is_tie())
        self.assertFalse(c.is_tie(four_winds=False))

    def test_discard(self):
        c = GameContext()
        c.players[0].hand.add_free_tiles([Tile.CHAR1, Tile.CHAR2, Tile.CHAR3,
                                          Tile.CHAR4, Tile.CHAR5, Tile.CHAR6,
                                          Tile.CHAR7])
        c.players[1].hand.add_free_tiles([Tile.CIRCLE1, Tile.CIRCLE2, Tile.CIRCLE3,
                                          Tile.CIRCLE4, Tile.CIRCLE5, Tile.CIRCLE6,
                                          Tile.CIRCLE7])
        c.players[2].hand.add_free_tiles([Tile.BAMBOO1, Tile.BAMBOO2, Tile.BAMBOO3,
                                          Tile.BAMBOO4, Tile.BAMBOO5, Tile.BAMBOO6,
                                          Tile.BAMBOO7])
        self.assertEqual(c.players[0].discarded, [])
        self.assertEqual(c.players[1].discarded, [])
        self.assertEqual(c.players[2].discarded, [])
        self.assertEqual(c.players[3].discarded, [])
        self.assertEqual(c.discarded_pool, [])

        c.discard(Tile.CHAR7, player_idx=0)
        c.discard(Tile.CHAR1, player_idx=0)
        c.discard(Tile.BAMBOO7, player_idx=2)
        c.discard(Tile.CIRCLE7, player_idx=1)
        c.discard(Tile.CIRCLE6, player_idx=1)

        c.cur_player_idx = 0
        c.player().hand.last_tile = Tile.RED
        c.discard(Tile.RED)

        with self.assertRaises(ValueError):
            c.discard(Tile.RED, player_idx=3)

        self.assertEqual(c.players[0].discarded, [Tile.CHAR7, Tile.CHAR1, Tile.RED])
        self.assertEqual(c.players[1].discarded, [Tile.CIRCLE7, Tile.CIRCLE6])
        self.assertEqual(c.players[2].discarded, [Tile.BAMBOO7])
        self.assertEqual(c.players[3].discarded, [])
        self.assertEqual(c.discarded_pool, [Tile.CHAR7, Tile.CHAR1, Tile.BAMBOO7,
                                            Tile.CIRCLE7, Tile.CIRCLE6, Tile.RED])

    def test_last_discarded(self):
        c = GameContext()
        self.assertIsNone(c.last_discarded())

        c.players[0].hand.add_free_tiles([Tile.CHAR1, Tile.CHAR2, Tile.CHAR3])
        c.discard(Tile.CHAR1, player_idx=0)
        self.assertEqual(c.last_discarded(), Tile.CHAR1)

        c.discard(Tile.CHAR2, player_idx=0)
        self.assertEqual(c.last_discarded(), Tile.CHAR2)

        c.discard(Tile.CHAR3, player_idx=0)
        self.assertEqual(c.last_discarded(), Tile.CHAR3)

    def test_remove_last_discarded(self):
        c = GameContext()
        c.discarded_pool += [Tile.RED, Tile.GREEN, Tile.WHITE]
        self.assertIsNone(c.remove_last_discarded())

        c.players[0].discarded.append(Tile.WHITE)
        self.assertEqual(c.remove_last_discarded(), Tile.WHITE)

        c.players[1].discarded.append(Tile.GREEN)
        self.assertIsNone(c.remove_last_discarded())
        self.assertEqual(c.remove_last_discarded(player_offset=1), Tile.GREEN)

        self.assertEqual(c.discarded_pool, [Tile.RED])
        self.assertEqual(c.players[0].discarded, [])
        self.assertEqual(c.players[1].discarded, [])

    def test_next_turn(self):
        c = GameContext()
        c.cur_player_idx = None
        c.last_player_idx = None
        c.next_turn()
        self.assertEqual(c.cur_player_idx, 0)
        self.assertIsNone(c.last_player_idx)

        c.next_turn()
        self.assertEqual(c.cur_player_idx, 1)
        self.assertEqual(c.last_player_idx, 0)

        c.next_turn()
        c.next_turn()
        self.assertEqual(c.cur_player_idx, 3)
        self.assertEqual(c.last_player_idx, 2)

        c.next_turn()
        c.next_turn()
        c.next_turn()
        self.assertEqual(c.cur_player_idx, 2)
        self.assertEqual(c.last_player_idx, 1)

    def test_set_turn(self):
        c = GameContext()
        c.set_turn(2)
        self.assertEqual(c.cur_player_idx, 2)
        self.assertEqual(c.last_player_idx, 0)

        c.set_turn(1)
        self.assertEqual(c.cur_player_idx, 1)
        self.assertEqual(c.last_player_idx, 2)
