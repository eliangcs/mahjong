import unittest

from mahjong import bots
from mahjong.types import GameContext, Tile


class TestDumbBot(unittest.TestCase):

    def setUp(self):
        self.bot = bots.get()

    def test_discard(self):
        c = GameContext()
        c.state = 'discarding'
        hand = c.player().hand
        hand.add_free_tiles([Tile.CHAR1, Tile.CHAR2, Tile.CHAR3])
        hand.last_tile = Tile.CHAR4
        self.assertEqual(self.bot.make_decision(c), Tile.CHAR4)

    def test_make_decision(self):
        c = GameContext()
        c.player().extra['viable_decisions'] = ['kong', 'pong', 'chow', 'skip']
        self.assertEqual(self.bot.make_decision(c), 'skip')

        c.player().extra.get('viable_decisions').append('win')
        self.assertEqual(self.bot.make_decision(c), 'win')

        del c.player().extra.get('viable_decisions')[:]
        self.assertIsNone(self.bot.make_decision(c))
