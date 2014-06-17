import unittest

from mahjong import algo
from mahjong.types import GameContext, Tile


class TestCanWin(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

        # wait for BAMBOO5
        self.context.players[0].hand.add_free_tiles([
            Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
            Tile.CHAR2, Tile.CHAR2, Tile.CHAR2,
            Tile.CHAR3, Tile.CHAR3, Tile.CHAR3,
            Tile.BAMBOO1, Tile.BAMBOO2, Tile.BAMBOO3, Tile.BAMBOO5
        ])

        # wait for BAMBOO1
        self.context.players[1].hand.add_free_tiles([
            Tile.BAMBOO1,
            Tile.CIRCLE4, Tile.CIRCLE4, Tile.CIRCLE4,
            Tile.BAMBOO5, Tile.BAMBOO5, Tile.BAMBOO5,
            Tile.BAMBOO7, Tile.BAMBOO7, Tile.BAMBOO7,
            Tile.CIRCLE8, Tile.CIRCLE8, Tile.CIRCLE8
        ])

        # wait for CHAR9 and BAMBOO1
        self.context.players[2].hand.add_free_tiles([
            Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
            Tile.CHAR9, Tile.CHAR9,
            Tile.BAMBOO1, Tile.BAMBOO1,
            Tile.WHITE, Tile.WHITE, Tile.WHITE,
            Tile.WEST, Tile.WEST, Tile.WEST
        ])

        # not ready
        self.context.players[3].hand.add_free_tiles([
            Tile.RED, Tile.WHITE, Tile.RED,
            Tile.GREEN, Tile.EAST, Tile.GREEN,
            Tile.SOUTH, Tile.SOUTH, Tile.SOUTH,
            Tile.BAMBOO1, Tile.BAMBOO2, Tile.BAMBOO3,
            Tile.CHAR9, Tile.CHAR3,
            Tile.CHAR4, Tile.CIRCLE1
        ])

    def test_declared_ready(self):
        self.context.players[0].extra['declared_ready'] = True
        self.context.players[0].extra['waiting_tiles'] = [Tile.EAST, Tile.NORTH]

        self.assertTrue(algo.can_win(self.context, player_idx=0, incoming_tile=Tile.EAST))
        self.assertTrue(algo.can_win(self.context, player_idx=0, incoming_tile=Tile.NORTH))
        self.assertTrue(algo.can_win(self.context, player_idx=0, incoming_tile=Tile.BAMBOO5))
        self.assertFalse(algo.can_win(self.context, player_idx=0, incoming_tile=Tile.BAMBOO4))
        self.assertFalse(algo.can_win(self.context, player_idx=0, incoming_tile=Tile.WEST))

    def test_general_winning_pattern(self):
        self.context.players[0].hand.last_tile = Tile.BAMBOO5
        self.assertTrue(algo.can_win(self.context, player_idx=0))

        self.context.players[0].hand.last_tile = Tile.BAMBOO1
        self.assertFalse(algo.can_win(self.context, player_idx=0))
        self.assertFalse(algo.can_win(self.context, player_idx=0, incoming_tile=Tile.RED))

        self.assertFalse(algo.can_win(self.context, 1, Tile.BAMBOO3))
        self.assertFalse(algo.can_win(self.context, 1, Tile.BAMBOO2))
        self.assertTrue(algo.can_win(self.context, 1, Tile.BAMBOO1))

        self.assertTrue(algo.can_win(self.context, 2, Tile.BAMBOO1))
        self.assertTrue(algo.can_win(self.context, 2, Tile.CHAR9))
        self.assertFalse(algo.can_win(self.context, 2, Tile.CIRCLE1))

        self.assertFalse(algo.can_win(self.context, 3, Tile.CHAR1))
        self.assertFalse(algo.can_win(self.context, 3, Tile.CIRCLE1))

    def test_winning_restriction(self):
        self.context.settings.patterns_win_filter += [
            'lack-a-suit', 'self-picked'
        ]

        self.assertFalse(algo.can_win(self.context, 0, Tile.BAMBOO5))

        self.context.players[0].hand.last_tile = Tile.BAMBOO5
        self.assertTrue(algo.can_win(self.context, 0))

        self.context.players[1].hand.last_tile = Tile.BAMBOO1
        self.assertTrue(algo.can_win(self.context, 1))

        self.context.players[1].hand.last_tile = None
        self.assertFalse(algo.can_win(self.context, 2, Tile.BAMBOO1))

        self.context.players[2].hand.last_tile = Tile.CHAR9
        self.assertFalse(algo.can_win(self.context, 2))

        self.context.players[2].hand.last_tile = Tile.BAMBOO1
        self.assertFalse(algo.can_win(self.context, 2))

        hand = self.context.players[2].hand
        hand.free_tiles = hand.free_tiles[:7]

        hand.last_tile = Tile.CHAR9
        self.assertTrue(algo.can_win(self.context, 2))

        hand.last_tile = Tile.BAMBOO1
        self.assertTrue(algo.can_win(self.context, 2))

        hand.last_tile = Tile.BAMBOO2
        self.assertFalse(algo.can_win(self.context, 2))

    def test_special_pattern(self):
        # eight- or seven-flowers
        self.assertFalse(algo.can_win(self.context, 2, Tile.RED))
        self.context.players[2].hand.flowers = Tile.FLOWERS
        self.assertTrue(algo.can_win(self.context, 2, Tile.RED))

    def test_illegal_arugments(self):
        self.context.cur_player_idx = None
        with self.assertRaises(ValueError):
            algo.can_win(self.context)

        self.context.cur_player_idx = 0
        with self.assertRaises(ValueError):
            algo.can_win(self.context)


class TestWaitingTiles(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

        # wait for BAMBOO5
        self.context.players[0].hand.add_free_tiles([
            Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
            Tile.CHAR2, Tile.CHAR2, Tile.CHAR2,
            Tile.CHAR3, Tile.CHAR3, Tile.CHAR3,
            Tile.BAMBOO1, Tile.BAMBOO2, Tile.BAMBOO3, Tile.BAMBOO5
        ])

        # wait for BAMBOO1
        self.context.players[1].hand.add_free_tiles([
            Tile.BAMBOO1,
            Tile.CIRCLE4, Tile.CIRCLE4, Tile.CIRCLE4,
            Tile.BAMBOO5, Tile.BAMBOO5, Tile.BAMBOO5,
            Tile.BAMBOO7, Tile.BAMBOO7, Tile.BAMBOO7,
            Tile.CIRCLE8, Tile.CIRCLE8, Tile.CIRCLE8
        ])

        # wait for CHAR9 and BAMBOO1
        self.context.players[2].hand.add_free_tiles([
            Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
            Tile.CHAR9, Tile.CHAR9,
            Tile.BAMBOO1, Tile.BAMBOO1,
            Tile.WHITE, Tile.WHITE, Tile.WHITE,
            Tile.WEST, Tile.WEST, Tile.WEST
        ])

        # not ready
        self.context.players[3].hand.add_free_tiles([
            Tile.RED, Tile.WHITE, Tile.RED,
            Tile.GREEN, Tile.EAST, Tile.GREEN,
            Tile.SOUTH, Tile.SOUTH, Tile.SOUTH,
            Tile.BAMBOO1, Tile.BAMBOO2, Tile.BAMBOO3,
            Tile.CHAR9, Tile.CHAR3,
            Tile.CHAR4, Tile.CIRCLE1
        ])

    def test_waiting_tiles(self):
        self.assertEqual(algo.waiting_tiles(self.context, 0), [Tile.BAMBOO5])
        self.assertEqual(algo.waiting_tiles(self.context, 1), [Tile.BAMBOO1])
        self.assertEqual(algo.waiting_tiles(self.context, 2), [Tile.CHAR9, Tile.BAMBOO1])
        self.assertFalse(algo.waiting_tiles(self.context, 3))

    def test_special_pattern(self):
        # seven flowers
        self.context.players[2].hand.flowers = Tile.FLOWERS[0:7]
        self.assertEqual(algo.waiting_tiles(self.context, 2), [Tile.CHAR9, Tile.BAMBOO1] + Tile.FLOWERS)


class TestReady(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

        # wait for BAMBOO5
        self.context.players[0].hand.add_free_tiles([
            Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
            Tile.CHAR2, Tile.CHAR2, Tile.CHAR2,
            Tile.CHAR3, Tile.CHAR3, Tile.CHAR3,
            Tile.BAMBOO1, Tile.BAMBOO2, Tile.BAMBOO3, Tile.BAMBOO5
        ])

        # wait for BAMBOO1
        self.context.players[1].hand.add_free_tiles([
            Tile.BAMBOO1,
            Tile.CIRCLE4, Tile.CIRCLE4, Tile.CIRCLE4,
            Tile.BAMBOO5, Tile.BAMBOO5, Tile.BAMBOO5,
            Tile.BAMBOO7, Tile.BAMBOO7, Tile.BAMBOO7,
            Tile.CIRCLE8, Tile.CIRCLE8, Tile.CIRCLE8
        ])

        # wait for CHAR9 and BAMBOO1
        self.context.players[2].hand.add_free_tiles([
            Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
            Tile.CHAR9, Tile.CHAR9,
            Tile.BAMBOO1, Tile.BAMBOO1,
            Tile.WHITE, Tile.WHITE, Tile.WHITE,
            Tile.WEST, Tile.WEST, Tile.WEST
        ])

        # not ready
        self.context.players[3].hand.add_free_tiles([
            Tile.RED, Tile.WHITE, Tile.RED,
            Tile.GREEN, Tile.EAST, Tile.GREEN,
            Tile.SOUTH, Tile.SOUTH, Tile.SOUTH,
            Tile.BAMBOO1, Tile.BAMBOO2, Tile.BAMBOO3,
            Tile.CHAR9, Tile.CHAR3,
            Tile.CHAR4, Tile.CIRCLE1
        ])

    def test_ready(self):
        self.assertTrue(algo.ready(self.context, 0))
        self.assertTrue(algo.ready(self.context, 1))
        self.assertTrue(algo.ready(self.context, 2))
        self.assertFalse(algo.ready(self.context, 3))


class TestSelectMelders(unittest.TestCase):

    def test_none_viable(self):
        viable_decisions = [None, None, None, None]
        player_decisions = [None, None, None, None]
        self.assertFalse(algo.select_melders(viable_decisions, player_decisions))

    def test_everybody_skips(self):
        viable_decisions = [
            ['win', 'chow', 'skip'],
            ['pong', 'skip'],
            ['win', 'skip'],
            ['win', 'skip']
        ]
        player_decisions = ['skip', 'skip', 'skip', 'skip']
        self.assertFalse(algo.select_melders(viable_decisions, player_decisions))

    def test_priority(self):
        viable_decisions = [
            None,
            ['win', 'chow', 'skip'],
            ['kong', 'skip'],
            ['win', 'skip']
        ]

        player_decisions = [None, 'chow', 'kong', 'win']
        self.assertEqual(algo.select_melders(viable_decisions, player_decisions),
                         [(3, 'win')])

        player_decisions = [None, 'chow', 'kong', 'skip']
        self.assertEqual(algo.select_melders(viable_decisions, player_decisions),
                         [(2, 'kong')])

        player_decisions = [None, 'chow', 'skip', 'skip']
        self.assertEqual(algo.select_melders(viable_decisions, player_decisions),
                         [(1, 'chow')])

    def test_multi_win(self):
        viable_decisions = [
            None,
            ['win', 'skip'],
            ['kong', 'skip'],
            ['win', 'skip']
        ]
        player_decisions = [None, 'win', 'kong', 'win']
        self.assertEqual(algo.select_melders(viable_decisions, player_decisions),
                         [(1, 'win'), (3, 'win')])
