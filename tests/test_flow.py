import copy
import unittest

from mahjong import flow
from mahjong.patterns import MatchResult
from mahjong.types import Hand, GameContext, GameSettings, Tile, TileGroup, Wall


class TestHandler(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()
        self.handler = flow.Handler()

    def test_default_implementation(self):
        with self.assertRaises(NotImplementedError):
            self.handler.handle(self.context)


class TestIllegalState(unittest.TestCase):

    def test_illegal_state(self):
        c = GameContext()
        c.state = 'no-such-state'
        with self.assertRaises(ValueError):
            flow.next(c)


class TestStartHandler(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()
        self.context.wall = Wall()

    def test_wall_shuffled(self):
        # get first ten tiles
        orig_tiles = [self.context.wall.tiles[i] for i in xrange(10)]
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'wall-built')

        # test if it's shuffled
        new_tiles = [self.context.wall.tiles[i] for i in xrange(10)]
        self.assertNotEqual(orig_tiles, new_tiles)

    def test_wall_complete(self):
        # test if wall gets reset
        self.context.wall.draw()
        self.assertEqual(self.context.wall.num_tiles(), 143)
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.wall.num_tiles(), 144)

    def test_illegal_case(self):
        self.context.wall = None
        context2 = self.context.clone()
        self.assertFalse(flow.next(self.context))
        self.assertEqual(self.context, context2)


class TestWallBuiltHandler(unittest.TestCase):

    def setUp(self):
        self.context = GameContext(settings=GameSettings())
        self.context.state = 'wall-built'

        # build wall
        self.context.wall = Wall()
        self.context.wall.shuffle()

    def test_deal_16_tiles(self):
        self.context.settings.num_hand_tiles = 16
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'dealt')
        self.assert_num_free_tiles(self.context, 16)

    def test_deal_13_tiles(self):
        self.context.settings.num_hand_tiles = 13
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'dealt')
        self.assert_num_free_tiles(self.context, 13)

    def test_illegal_case(self):
        self.context.wall.draw()
        context2 = self.context.clone()
        self.assertFalse(flow.next(self.context))
        self.assertEqual(self.context, context2)

    def assert_num_free_tiles(self, context, num_tiles):
        self.assertEqual(len(context.players[0].hand.free_tiles), num_tiles)
        self.assertEqual(len(context.players[1].hand.free_tiles), num_tiles)
        self.assertEqual(len(context.players[2].hand.free_tiles), num_tiles)
        self.assertEqual(len(context.players[3].hand.free_tiles), num_tiles)
        self.assertEqual(context.players[0].hand.fixed_groups, [])
        self.assertEqual(context.players[1].hand.fixed_groups, [])
        self.assertEqual(context.players[2].hand.fixed_groups, [])
        self.assertEqual(context.players[3].hand.fixed_groups, [])
        self.assertEqual(context.players[0].hand.flowers, [])
        self.assertEqual(context.players[1].hand.flowers, [])
        self.assertEqual(context.players[2].hand.flowers, [])
        self.assertEqual(context.players[3].hand.flowers, [])
        self.assertIsNone(context.players[0].hand.last_tile)
        self.assertIsNone(context.players[1].hand.last_tile)
        self.assertIsNone(context.players[2].hand.last_tile)
        self.assertIsNone(context.players[3].hand.last_tile)


class TestDealtHandler(unittest.TestCase):

    def setUp(self):
        self.context = GameContext(settings=GameSettings())
        self.context.state = 'dealt'

        # build wall
        self.context.wall = Wall()
        self.context.wall.shuffle()

        # deal some flowers to players
        self.context.players[0].hand.add_free_tile(Tile.PLUM)
        self.context.players[0].hand.add_free_tile(Tile.ORCHID)
        self.context.players[1].hand.add_free_tile(Tile.BAMBOO)
        self.context.players[1].hand.add_free_tile(Tile.CHRYSANTH)
        self.context.players[3].hand.add_free_tile(Tile.SPRING)
        self.context.players[3].hand.add_free_tile(Tile.SUMMER)
        self.context.players[3].hand.add_free_tile(Tile.AUTUMN)
        self.context.players[3].hand.add_free_tile(Tile.WINTER)

        # remove flowers in wall
        for flower in Tile.FLOWERS:
            self.context.wall.tiles.remove(flower)

        # add more tiles until each hand has 16 tiles
        for player in self.context.players:
            hand = player.hand
            while len(hand.free_tiles) < 16:
                tile = self.context.wall.draw()
                hand.add_free_tile(tile)

    def test_replace_flowers(self):
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'drawing')
        self.assertEqual(self.context.players[0].hand.flowers, [Tile.PLUM, Tile.ORCHID])
        self.assertEqual(self.context.players[1].hand.flowers, [Tile.BAMBOO, Tile.CHRYSANTH])
        self.assertEqual(self.context.players[2].hand.flowers, [])
        self.assertEqual(self.context.players[3].hand.flowers, [Tile.SPRING, Tile.SUMMER, Tile.AUTUMN, Tile.WINTER])

        # free_tiles should have 13 tiles and have no flowers
        self.assertEqual(len(self.context.players[0].hand.free_tiles), 16)
        self.assertEqual(len(self.context.players[1].hand.free_tiles), 16)
        self.assertEqual(len(self.context.players[2].hand.free_tiles), 16)
        self.assertEqual(len(self.context.players[3].hand.free_tiles), 16)
        self.assertEqual(filter(lambda x: x.is_general_flower(), self.context.players[0].hand.free_tiles), [])
        self.assertEqual(filter(lambda x: x.is_general_flower(), self.context.players[1].hand.free_tiles), [])
        self.assertEqual(filter(lambda x: x.is_general_flower(), self.context.players[2].hand.free_tiles), [])
        self.assertEqual(filter(lambda x: x.is_general_flower(), self.context.players[3].hand.free_tiles), [])

    def test_illegal_case(self):
        self.context.wall.draw()
        context2 = self.context.clone()
        self.assertFalse(flow.next(self.context))
        self.assertEqual(self.context, context2)


class TestDrawingHandler(unittest.TestCase):

    def setUp(self):
        gs = GameSettings()
        gs.tie_wall = 16
        gs.tie_wall_per_kong = 2

        self.context = GameContext(settings=gs)
        self.context.state = 'drawing'

        # build wall
        self.context.wall = Wall()
        self.context.wall.shuffle()

        hands = [player.hand for player in self.context.players]

        hands[0].free_tiles = [Tile.CHAR1]
        hands[1].free_tiles = [Tile.CHAR2]
        hands[2].free_tiles = [Tile.CHAR3]
        hands[3].free_tiles = [Tile.CHAR4]

        for __ in xrange(4):
            self.context.wall.draw()

    def test_initial_drawing(self):
        hand = self.context.player().hand

        # initial condition assertion
        self.assertEqual(self.context.cur_player_idx, 0)
        self.assertIsNone(self.context.last_player_idx)
        self.assertIsNone(hand.last_tile)

        orig_num_tiles = self.context.wall.num_tiles()
        self.assertTrue(flow.next(self.context))

        self.assertEqual(self.context.wall.num_tiles(), orig_num_tiles - 1)
        self.assertTrue(hand.last_tile)
        self.assertEqual(self.context.cur_player_idx, 0)
        self.assertIsNone(self.context.last_player_idx)
        self.assertEqual(self.context.state, 'drawn')

    def test_middle_game(self):
        self.context.cur_player_idx = 2
        self.context.last_player_idx = 0
        hand = self.context.player().hand

        orig_num_tiles = self.context.wall.num_tiles()
        self.assertIsNone(hand.last_tile)
        self.assertTrue(flow.next(self.context))

        self.assertEqual(self.context.wall.num_tiles(), orig_num_tiles - 1)
        self.assertTrue(hand.last_tile)
        self.assertEqual(self.context.cur_player_idx, 2)
        self.assertEqual(self.context.last_player_idx, 0)
        self.assertEqual(self.context.state, 'drawn')

    def test_seven_flowers_1(self):
        # Scenario: Player 3 got seven flowers already. And player 1
        # draws another flower.

        # let player 3 have seven flowers
        self.context.players[3].hand.flowers = Tile.FLOWERS[0:7]

        # player 1 draws a flower -> player 3 can win
        draw_for_player(self.context, 1, last_player_idx=0, tile=Tile.WINTER)
        self.context.player().hand.move_flowers()
        self.context.player().extra['flowered'] = True

        # player 3 hasn't make a decision
        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [None, None, None, ['win', 'skip']])

        # player 3 decides to win
        self.context.players[3].decision = 'win'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'drawn')
        self.assertEqual(self.context.cur_player_idx, 3)
        self.assertEqual(self.context.last_player_idx, 1)
        self.assertTrue(self.context.player().hand.last_tile)
        self.assertEqual(self.context.extra.get('flower_chucker'), 1)
        self.assertEqual(len(self.context.player().hand.flowers), 8)

        # check if intermediate data is cleaned up
        self.assertEqual(len(self.context.extra), 1)
        self.assertEqual(self.context.players[1].extra, {})
        self.assertEqual(self.context.players[3].extra, { 'flowered': True })

    def test_seven_flowers_2(self):
        # Scenario: Player 2 got six flowers and player 3 got one
        # flower already. And player 2 draws another flower.

        # player 2 has six flowers, player 3 has one flower
        self.context.players[2].hand.flowers = Tile.FLOWERS[0:6]
        self.context.players[3].hand.add_flower(Tile.FLOWERS[6])

        # player 2 draws a flower -> player 2 can rob player 3's flower
        draw_for_player(self.context, 2, last_player_idx=1, tile=Tile.FLOWERS[7])
        self.context.player().hand.move_flowers()
        self.context.player().extra['flowered'] = True

        # player 2 hasn't make decision
        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [None, None, ['win', 'skip'], None])

        # player 2 decides to win
        self.context.players[2].decision = 'win'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'drawn')
        self.assertEqual(self.context.cur_player_idx, 2)
        self.assertEqual(self.context.last_player_idx, 1)
        self.assertTrue(self.context.player().hand.last_tile)
        self.assertEqual(self.context.extra.get('flower_chucker'), 3)
        self.assertEqual(len(self.context.player().hand.flowers), 8)

        # check if intermediate data is cleaned up
        self.assertEqual(len(self.context.extra), 1)
        self.assertEqual(self.context.players[2].extra, { 'flowered': True })
        self.assertEqual(self.context.players[3].extra, {})

    def test_seven_flowers_no_one_can_win(self):
        # Scenario: Player 3 has six flowers. And player 1 draws a flower.
        # Nothing should happend.

        # let player 3 have six flowers
        self.context.players[3].hand.flowers = Tile.FLOWERS[0:6]

        # player 1 draws a flower
        draw_for_player(self.context, 1, last_player_idx=0, tile=Tile.WINTER)
        self.context.player().hand.move_flowers()
        self.context.player().extra['flowered'] = True

        num_tiles_before = self.context.wall.num_tiles()
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'drawn')
        self.assertEqual(self.context.cur_player_idx, 1)
        self.assertNotEqual(self.context.player().hand.last_tile, Tile.WINTER)
        self.assertEqual(self.context.wall.num_tiles(), num_tiles_before - 1)

        # check if intermediate data is cleaned up
        self.assertEqual(self.context.extra, {})
        self.assertEqual(self.context.player().extra, { 'flowered': True })

    def test_seven_flowers_declared_ready(self):
        # let player 3 have seven flowers and declare ready
        self.context.players[3].hand.flowers = Tile.FLOWERS[0:7]
        self.context.players[3].extra['declared_ready'] = True

        # player 2 draws a flower -> player 3 can win
        draw_for_player(self.context, 2, last_player_idx=3, tile=Tile.WINTER)
        self.context.player().hand.move_flowers()
        self.context.player().extra['flowered'] = True

        # player 3 wins without making a decision since he declared ready
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'drawn')
        self.assertEqual(self.context.cur_player_idx, 3)
        self.assertEqual(self.context.last_player_idx, 2)
        self.assertTrue(self.context.player().hand.last_tile)
        self.assertEqual(self.context.extra.get('flower_chucker'), 2)

        # check if intermediate data is cleaned up
        self.assertEqual(len(self.context.extra), 1)
        self.assertEqual(self.context.players[2].extra, {})

    def test_seven_flowers_bot(self):
        # let player 3 have seven flowers and declare ready
        self.context.players[3].hand.flowers = Tile.FLOWERS[0:7]
        self.context.players[3].extra['bot'] = True

        # player 2 draws a flower -> player 3 can win
        draw_for_player(self.context, 2, last_player_idx=3, tile=Tile.WINTER)
        self.context.player().hand.move_flowers()
        self.context.player().extra['flowered'] = True

        # bot makes decision for player 3
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'drawn')
        self.assertEqual(self.context.cur_player_idx, 3)
        self.assertEqual(self.context.last_player_idx, 2)
        self.assertTrue(self.context.player().hand.last_tile)
        self.assertEqual(self.context.extra.get('flower_chucker'), 2)

        # check if intermediate data is cleaned up
        self.assertEqual(len(self.context.extra), 1)
        self.assertEqual(self.context.players[2].extra, {})

    def test_wall_tie(self):
        self.context.cur_player_idx = 3
        self.context.last_player_idx = 2
        hand = self.context.player().hand

        # give player 3 two fake kongs
        hand.fixed_groups.append(TileGroup([Tile.RED] * 4, TileGroup.KONG_CONCEALED))
        hand.fixed_groups.append(TileGroup([Tile.GREEN] * 4, TileGroup.KONG_EXPOSED))

        while self.context.wall.num_tiles() != 21:
            self.context.wall.draw()

        self.assertTrue(flow.next(self.context))

        self.assertEqual(self.context.state, 'drawn')
        self.assertTrue(hand.last_tile)

        self.context.state = 'drawing'
        hand.last_tile = None

        self.assertTrue(flow.next(self.context))

        self.assertEqual(self.context.state, 'end')
        self.assertFalse(self.context.winners)
        self.assertEqual(self.context.extra.get('tie_type'), 'wall')

    def test_bad_context(self):
        self.context.player().hand.last_tile = Tile.RED
        context2 = self.context.clone()
        self.assertFalse(flow.next(self.context))
        self.assertEqual(self.context, context2)

        self.context = context2
        self.context.cur_player_idx = 2
        self.context.player().extra['flowered'] = True
        self.assertFalse(flow.next(self.context))


class TestDrawnHandler(unittest.TestCase):

    def setUp(self):
        gs = GameSettings()
        gs.tie_wall = 16
        gs.tie_wall_per_kong = 1
        gs.tie_on_4_kongs = True

        self.context = GameContext(settings=gs)
        self.context.state = 'drawn'

        # build wall
        self.context.wall = Wall()
        self.context.wall.shuffle()

        hands = [p.hand for p in self.context.players]

        # lousy hand for player 0
        hands[0].add_free_tiles([Tile.CHAR2, Tile.CHAR4, Tile.CHAR9,
                                 Tile.CIRCLE9, Tile.BAMBOO1, Tile.BAMBOO4,
                                 Tile.EAST, Tile.SOUTH, Tile.WEST,
                                 Tile.NORTH, Tile.RED, Tile.GREEN, Tile.GREEN])
        # ready hand for player 1 - waiting for CHAR6 and CHAR9
        hands[1].add_free_tiles([Tile.CHAR2, Tile.CHAR2, Tile.CHAR7,
                                 Tile.CHAR8, Tile.BAMBOO2, Tile.BAMBOO3,
                                 Tile.BAMBOO4, Tile.SOUTH, Tile.SOUTH,
                                 Tile.SOUTH, Tile.WHITE, Tile.WHITE, Tile.WHITE])
        # lousy hand for player 2
        hands[2].add_free_tiles([Tile.CIRCLE1, Tile.CIRCLE2, Tile.CIRCLE3,
                                 Tile.BAMBOO5, Tile.BAMBOO6, Tile.BAMBOO7,
                                 Tile.BAMBOO8, Tile.BAMBOO9, Tile.BAMBOO9,
                                 Tile.EAST, Tile.EAST, Tile.WEST, Tile.NORTH])
        # ready hand for player 3 - waiting for CHAR5 and CIRCLE3
        hands[3].add_free_tiles([Tile.CHAR5, Tile.CHAR5, Tile.CHAR6,
                                 Tile.CHAR7, Tile.CHAR8, Tile.CIRCLE3,
                                 Tile.CIRCLE3, Tile.BAMBOO2, Tile.BAMBOO3,
                                 Tile.BAMBOO4, Tile.BAMBOO6, Tile.BAMBOO7, Tile.BAMBOO8])

        # remove same number of tiles dealt
        for __ in xrange(52):
            self.context.wall.draw()

    def test_4_kong_concealed_win(self):
        self.context.settings.patterns_win.append('four-kongs')

        # player 2 has 3 kongs already, and he draws another EAST for
        # him to make the 4th kong
        self.context.players[2].hand.fixed_groups = [
            TileGroup([Tile.CIRCLE1] * 4, TileGroup.KONG_EXPOSED),
            TileGroup([Tile.CIRCLE3] * 4, TileGroup.KONG_CONCEALED),
            TileGroup([Tile.CIRCLE5] * 4, TileGroup.KONG_EXPOSED)
        ]
        self.context.players[2].hand.add_free_tile(Tile.EAST)
        draw_for_player(self.context, 2, last_player_idx=3, tile=Tile.EAST)

        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [None, None, ['win', 'skip'], None])

        self.context.players[2].decision = 'win'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertEqual(self.context.winners, [2])
        self.assertEqual(self.context.players[2].extra.get('win_type'), 'self-picked')

    def test_4_kong_exposed_win(self):
        self.context.settings.patterns_win.append('four-kongs')

        # player 2 has 3 kongs and 1 pong already, and he draws another WHITE for
        # him to make an appended kong
        self.context.players[2].hand.fixed_groups = [
            TileGroup([Tile.CIRCLE1] * 4, TileGroup.KONG_EXPOSED),
            TileGroup([Tile.CIRCLE3] * 4, TileGroup.KONG_CONCEALED),
            TileGroup([Tile.WHITE] * 3, TileGroup.PONG),
            TileGroup([Tile.CIRCLE5] * 4, TileGroup.KONG_EXPOSED)
        ]
        draw_for_player(self.context, 2, last_player_idx=3, tile=Tile.WHITE)

        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [None, None, ['win', 'skip'], None])

        # player 2 can win with an appended kong, but it's possible that
        # somebody can rob the kong, so the state is switched to 'self-konging'
        # instead of 'end'
        self.context.players[2].decision = 'win'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'self-konging')
        self.assertEqual(self.context.cur_player_idx, 2)
        self.assertEqual(self.context.player().hand.last_tile, Tile.WHITE)

    def test_eight_flowers(self):
        # let player 1 have seven flowers
        self.context.players[1].hand.flowers = Tile.FLOWERS[0:7]

        # player 1 draws the 8th flower
        draw_for_player(self.context, 1, last_player_idx=0, tile=Tile.CHRYSANTH)

        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'drawing')
        self.assertEqual(len(self.context.player().hand.flowers), 8)
        self.assertFalse(self.context.player().hand.last_tile)
        self.assertTrue(self.context.player().extra.get('flowered'))

        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'drawn')

        # assume player draws a RED which he cannot win with
        self.context.player().hand.last_tile = Tile.RED
        context2 = self.context.clone()

        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [None, ['win', 'skip'], None, None])

        self.context.players[1].decision = 'win'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertEqual(self.context.winners, [1])
        self.assertEqual(self.context.players[1].extra.get('win_type'), 'flower-won')

        # test it again, this time player has a winning hand
        self.context = context2
        self.context.player().hand.last_tile = Tile.CHAR6
        self.context.players[1].decision = 'win'

        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertEqual(self.context.winners, [1])
        self.assertEqual(self.context.players[1].extra.get('win_type'), 'self-picked')

    def test_seven_flowers(self):
        # player 3 has eight flowers, one of them was robbed from player 0
        self.context.players[3].hand.flowers = copy.copy(Tile.FLOWERS)
        self.context.extra['flower_chucker'] = 0
        draw_for_player(self.context, 3, last_player_idx=2, tile=Tile.CIRCLE4)

        context2 = self.context.clone()

        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [None, None, None, ['win', 'skip']])

        self.context.players[3].decision = 'win'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertEqual(self.context.winners, [3])
        self.assertEqual(self.context.players[3].extra.get('win_type'), 'flower-won')
        self.assertEqual(self.context.extra.get('flower_chucker'), 0)

        # test it again, this time player has a winning hand
        self.context = context2
        self.context.player().hand.last_tile = Tile.CHAR5
        self.context.player().decision = 'win'

        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertEqual(self.context.winners, [3])
        self.assertEqual(self.context.players[3].extra.get('win_type'), 'self-picked')
        self.assertEqual(self.context.extra.get('flower_chucker'), 0)

    def test_seven_flowers_plus_self_pick(self):
        # player 1 has eight flowers, one of them was robbed from player 3
        # and player 1 also gets a winning hand by self-picking
        self.context.players[1].hand.flowers = copy.copy(Tile.FLOWERS)
        self.context.extra['flower_chucker'] = 3
        draw_for_player(self.context, 1, last_player_idx=0, tile=Tile.CHAR9)

        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [None, ['win', 'skip'], None, None])

        self.context.players[1].decision = 'win'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertEqual(self.context.winners, [1])
        self.assertEqual(self.context.players[1].extra.get('win_type'), 'self-picked')
        self.assertIsNone(self.context.players[1].extra.get('chucker'))
        self.assertEqual(self.context.extra.get('flower_chucker'), 3)

    def test_flower(self):
        draw_for_player(self.context, 3, last_player_idx=2, tile=Tile.SUMMER)
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'drawing')
        self.assertIsNone(self.context.player().hand.last_tile)
        self.assertIn(Tile.SUMMER, self.context.player().hand.flowers)

    def test_no_choices_but_skip(self):
        draw_for_player(self.context, 2, last_player_idx=1, tile=Tile.CIRCLE9)
        self.context.player().decision = 'doesnt-matter'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'discarding')
        self.assertEqual(self.context.cur_player_idx, 2)
        self.assertEqual(self.context.player().hand.last_tile, Tile.CIRCLE9)

    def test_self_pick(self):
        draw_for_player(self.context, 3, last_player_idx=2, tile=Tile.CIRCLE3)
        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [None, None, None, ['win', 'skip']])

        self.context.player().decision = 'win'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertEqual(self.context.winners, [3])
        self.assertEqual(self.context.players[3].extra.get('win_type'), 'self-picked')

    def test_appended_kong(self):
        self.context.players[2].hand.pong(Tile.EAST)
        draw_for_player(self.context, 2, last_player_idx=1, tile=Tile.EAST)
        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [None, None, ['kong', 'skip'], None])

        self.context.player().decision = 'kong'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'self-konging')
        self.assertEqual(self.context.cur_player_idx, 2)
        self.assertEqual(self.context.players[2].hand.last_tile, Tile.EAST)

    def test_concealed_kong(self):
        self.context.players[0].hand.free_tiles[10] = Tile.GREEN
        draw_for_player(self.context, 0, last_player_idx=1, tile=Tile.GREEN)
        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [['kong', 'skip'], None, None, None])

        self.context.player().decision = 'kong'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'self-konging')
        self.assertEqual(self.context.cur_player_idx, 0)
        self.assertEqual(self.context.players[0].hand.last_tile, Tile.GREEN)

    def test_skip_self_pick(self):
        draw_for_player(self.context, 1, last_player_idx=0, tile=Tile.CHAR6)
        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [None, ['win', 'skip'], None, None])

        self.context.player().decision = 'skip'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'discarding')
        self.assertEqual(self.context.cur_player_idx, 1)
        self.assertEqual(self.context.player().hand.last_tile, Tile.CHAR6)

    def test_skip_kong(self):
        self.context.players[3].hand.pong(Tile.CHAR5)
        draw_for_player(self.context, 3, last_player_idx=1, tile=Tile.CHAR5)
        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [None, None, None, ['kong', 'skip']])

        self.context.player().decision = 'skip'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'discarding')
        self.assertEqual(self.context.cur_player_idx, 3)
        self.assertEqual(self.context.player().hand.last_tile, Tile.CHAR5)

    def test_declared_ready_win(self):
        self.context.players[0].extra['declared_ready'] = True
        self.context.players[0].extra['waiting_tiles'] = [Tile.RED, Tile.GREEN]
        draw_for_player(self.context, 0, last_player_idx=3, tile=Tile.RED)
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertEqual(self.context.winners, [0])
        self.assertEqual(self.context.players[0].extra.get('win_type'), 'self-picked')

    def test_declared_ready_skip(self):
        self.context.players[1].extra['declared_ready'] = True
        self.context.players[1].extra['waiting_tiles'] = [Tile.RED, Tile.GREEN]
        draw_for_player(self.context, 1, last_player_idx=0, tile=Tile.WHITE)
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'discarding')
        self.assertEqual(self.context.cur_player_idx, 1)
        self.assertEqual(self.context.player().hand.last_tile, Tile.WHITE)

    def test_bot_always_chooses_to_win(self):
        draw_for_player(self.context, 3, last_player_idx=2, tile=Tile.CIRCLE3)
        self.context.players[3].extra['bot'] = True
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertEqual(self.context.winners, [3])
        self.assertEqual(self.context.players[3].extra.get('win_type'), 'self-picked')

    def test_bot_doesnt_kong(self):
        self.context.players[3].hand.pong(Tile.CHAR5)
        draw_for_player(self.context, 3, last_player_idx=1, tile=Tile.CHAR5)
        self.context.players[3].extra['bot'] = True
        self.assertTrue(self.context.state, 'discarding')
        self.assertEqual(self.context.cur_player_idx, 3)
        self.assertEqual(self.context.player().hand.last_tile, Tile.CHAR5)

    def test_bad_context(self):
        self.assertFalse(flow.next(self.context))


class TestSelfKongingHandler(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()
        self.context.state = 'self-konging'
        self.context.num_hand_tiles = 13

        # build wall
        self.context.wall = Wall()

        hands = [p.hand for p in self.context.players]

        # player 0 almost finishes four kongs
        hands[0].add_free_tiles([Tile.NORTH, Tile.NORTH, Tile.NORTH, Tile.EAST])
        hands[0].fixed_groups += [
            TileGroup([Tile.RED] * 4, TileGroup.KONG_EXPOSED),
            TileGroup([Tile.GREEN] * 4, TileGroup.KONG_EXPOSED),
            TileGroup([Tile.CHAR6] * 3, TileGroup.PONG)
        ]

        # player 1 - waiting for CHAR6 and CHAR9
        hands[1].add_free_tiles([Tile.CHAR2, Tile.CHAR2, Tile.CHAR7,
                                 Tile.CHAR8, Tile.BAMBOO2, Tile.BAMBOO3,
                                 Tile.BAMBOO4, Tile.SOUTH, Tile.SOUTH,
                                 Tile.SOUTH, Tile.WHITE, Tile.WHITE, Tile.WHITE])

        # player 2 - lousy hand
        hands[2].add_free_tiles([Tile.CIRCLE1, Tile.CIRCLE2, Tile.CIRCLE3,
                                 Tile.BAMBOO5, Tile.BAMBOO6, Tile.BAMBOO7,
                                 Tile.BAMBOO8, Tile.BAMBOO9, Tile.BAMBOO9,
                                 Tile.EAST, Tile.EAST, Tile.WEST, Tile.NORTH])

        # player 3 - waiting for CHAR3 and CHAR6
        hands[3].add_free_tiles([Tile.CHAR5, Tile.CHAR5, Tile.CHAR4,
                                 Tile.CHAR5, Tile.CIRCLE3, Tile.CIRCLE3,
                                 Tile.CIRCLE3, Tile.BAMBOO2, Tile.BAMBOO3,
                                 Tile.BAMBOO4, Tile.BAMBOO6, Tile.BAMBOO7, Tile.BAMBOO8])

    def test_no_one_can_rob(self):
        draw_for_player(self.context, 0, last_player_idx=3, tile=Tile.NORTH)
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'drawing')
        self.assertEqual(self.context.cur_player_idx, 0)
        self.assertIsNone(self.context.player().hand.last_tile)
        self.assertIn(TileGroup([Tile.NORTH] * 4, TileGroup.KONG_CONCEALED),
                      self.context.player().hand.fixed_groups)

    def test_one_rob(self):
        # change player 0's CHAR6 triplet to CHAR3 triplet
        self.context.players[0].hand.fixed_groups[2].tiles = [Tile.CHAR3] * 3

        draw_for_player(self.context, 0, last_player_idx=3, tile=Tile.CHAR3)
        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [None, None, None, ['win', 'skip']])

        self.context.players[3].decision = 'win'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertEqual(self.context.winners, [3])
        self.assertEqual(self.context.players[3].extra.get('win_type'), 'robbed')
        self.assertEqual(self.context.players[3].extra.get('chucker'), 0)

    def test_multi_robs(self):
        self.context.settings.multi_winners = True

        draw_for_player(self.context, 0, last_player_idx=3, tile=Tile.CHAR6)
        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [None, ['win', 'skip'], None, ['win', 'skip']])

        self.context.players[1].decision = 'win'
        self.context.players[3].decision = 'win'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertEqual(self.context.winners, [1, 3])
        self.assertEqual(self.context.players[1].extra.get('win_type'), 'robbed')
        self.assertEqual(self.context.players[1].extra.get('chucker'), 0)
        self.assertEqual(self.context.players[3].extra.get('win_type'), 'robbed')
        self.assertEqual(self.context.players[3].extra.get('chucker'), 0)

    def test_multi_robs_but_only_one_allowed(self):
        draw_for_player(self.context, 0, last_player_idx=3, tile=Tile.CHAR6)
        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [None, ['win', 'skip'], None, ['win', 'skip']])

        self.context.players[1].decision = 'win'
        self.context.players[3].decision = 'win'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertEqual(self.context.winners, [1])
        self.assertEqual(self.context.players[1].extra.get('win_type'), 'robbed')
        self.assertEqual(self.context.players[1].extra.get('chucker'), 0)

    def test_4_kong_tie(self):
        draw_for_player(self.context, 0, last_player_idx=3, tile=Tile.CHAR6)
        self.context.players[0].hand.kong_from_self()

        self.context.settings.tie_on_4_kongs = False
        orig_context = self.context.clone()

        draw_for_player(self.context, 1, last_player_idx=0, tile=Tile.WHITE)
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'drawing')
        self.assertEqual(self.context.cur_player_idx, 1)
        self.assertIsNone(self.context.player().hand.last_tile)

        # use the same context again but with tie_on_4_kongs turned on
        self.context = orig_context
        self.context.settings.tie_on_4_kongs = True

        draw_for_player(self.context, 1, last_player_idx=0, tile=Tile.WHITE)
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertFalse(self.context.winners)
        self.assertEqual(self.context.extra.get('tie_type'), '4-kong')

    def test_4_kong_win(self):
        self.context.settings.patterns_win.append('four-kongs')

        # player 0 makes the 3rd kong
        draw_for_player(self.context, 0, last_player_idx=3, tile=Tile.NORTH)
        self.context.players[0].hand.kong_from_self()

        # player 0 has a CHAR6 pong, and he draws another CHAR6
        # player 1 and 3 also wait for CHAR6
        draw_for_player(self.context, 0, last_player_idx=3, tile=Tile.CHAR6)
        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [None, ['win', 'skip'], None, ['win', 'skip']])

        # player 1 and 3 skip
        self.context.players[1].decision = 'skip'
        self.context.players[3].decision = 'skip'

        # player 0 wins with 4 kongs
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertEqual(self.context.winners, [0])
        self.assertEqual(self.context.players[0].extra.get('win_type'), 'self-picked')

    def test_bad_context(self):
        context2 = self.context.clone()
        self.assertFalse(flow.next(self.context))
        self.assertEqual(self.context, context2)

        self.context.player().hand.last_tile = Tile.SOUTH
        context2 = self.context.clone()
        self.assertFalse(flow.next(self.context))
        self.assertEqual(self.context, context2)


class TestDiscardingHandler(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()
        self.context.state = 'discarding'
        self.context.wall = Wall()

        hands = [p.hand for p in self.context.players]

        # lousy hand for player 0
        hands[0].add_free_tiles([Tile.CHAR2, Tile.CHAR4, Tile.CHAR9,
                                 Tile.CIRCLE9, Tile.BAMBOO1, Tile.BAMBOO4,
                                 Tile.EAST, Tile.SOUTH, Tile.WEST,
                                 Tile.NORTH, Tile.RED, Tile.GREEN, Tile.GREEN])
        # ready hand for player 1 - waiting for CHAR6 and CHAR9
        hands[1].add_free_tiles([Tile.CHAR2, Tile.CHAR2, Tile.CHAR7,
                                 Tile.CHAR8, Tile.BAMBOO2, Tile.BAMBOO3,
                                 Tile.BAMBOO4, Tile.SOUTH, Tile.SOUTH,
                                 Tile.SOUTH, Tile.WHITE, Tile.WHITE, Tile.WHITE])
        # lousy hand for player 2
        hands[2].add_free_tiles([Tile.CIRCLE1, Tile.CIRCLE2, Tile.CIRCLE3,
                                 Tile.BAMBOO5, Tile.BAMBOO6, Tile.BAMBOO7,
                                 Tile.BAMBOO8, Tile.BAMBOO9, Tile.BAMBOO9,
                                 Tile.EAST, Tile.EAST, Tile.WEST, Tile.NORTH])
        # ready hand for player 3 - waiting for CHAR5 and CIRCLE3
        hands[3].add_free_tiles([Tile.CHAR5, Tile.CHAR5, Tile.CHAR6,
                                 Tile.CHAR7, Tile.CHAR8, Tile.CIRCLE3,
                                 Tile.CIRCLE3, Tile.BAMBOO2, Tile.BAMBOO3,
                                 Tile.BAMBOO4, Tile.BAMBOO6, Tile.BAMBOO7, Tile.BAMBOO8])

    def test_declared_ready_discard(self):
        self.context.players[0].extra['declared_ready'] = True
        draw_for_player(self.context, 0, last_player_idx=3, tile=Tile.WHITE)
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'discarded')
        self.assertIsNone(self.context.player().hand.last_tile)
        self.assertEqual(self.context.player().discarded, [Tile.WHITE])
        self.assertEqual(self.context.last_discarded(), Tile.WHITE)

    def test_discarding_hints(self):
        # player 1 draws and discards CHAR8
        draw_for_player(self.context, 1, last_player_idx=0, tile=Tile.CHAR8)
        orig_context = self.context.clone()

        hand = self.context.player().hand
        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions,
                         [None, set(hand.free_tiles + [hand.last_tile]), None, None])
        self.assertEqual(self.context, orig_context)

    def test_discard_tiles(self):
        # player 1 draws and discards CHAR8
        draw_for_player(self.context, 1, last_player_idx=0, tile=Tile.CHAR8)
        self.context.player().decision = Tile.CHAR8
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'discarded')
        self.assertIsNone(self.context.player().hand.last_tile)
        self.assertEqual(self.context.players[0].discarded, [])
        self.assertEqual(self.context.players[1].discarded, [Tile.CHAR8])
        self.assertEqual(self.context.players[2].discarded, [])
        self.assertEqual(self.context.players[3].discarded, [])
        self.assertEqual(self.context.discarded_pool, [Tile.CHAR8])
        self.assertEqual(self.context.player().hand.free_tiles,
                         [Tile.CHAR2, Tile.CHAR2, Tile.CHAR7,
                          Tile.CHAR8, Tile.BAMBOO2, Tile.BAMBOO3,
                          Tile.BAMBOO4, Tile.SOUTH, Tile.SOUTH,
                          Tile.SOUTH, Tile.WHITE, Tile.WHITE, Tile.WHITE])
        self.assertIsNone(self.context.player().decision)

        # if player hasn't make decision, flow.next() won't change the context
        self.context.state = 'discarding'
        draw_for_player(self.context, 2, last_player_idx=1, tile=Tile.CHAR9)
        self.context.player().decision = None
        self.assertFalse(flow.next(self.context))
        self.assertEqual(self.context.state, 'discarding')

        # player 2 discards EAST
        self.context.player().decision = Tile.EAST
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'discarded')
        self.assertEqual(self.context.players[0].discarded, [])
        self.assertEqual(self.context.players[1].discarded, [Tile.CHAR8])
        self.assertEqual(self.context.players[2].discarded, [Tile.EAST])
        self.assertEqual(self.context.players[3].discarded, [])
        self.assertEqual(self.context.discarded_pool, [Tile.CHAR8, Tile.EAST])
        self.assertIsNone(self.context.player().hand.last_tile)
        self.assertEqual(self.context.player().hand.free_tiles,
                         [Tile.CHAR9, Tile.CIRCLE1, Tile.CIRCLE2, Tile.CIRCLE3,
                          Tile.BAMBOO5, Tile.BAMBOO6, Tile.BAMBOO7,
                          Tile.BAMBOO8, Tile.BAMBOO9, Tile.BAMBOO9,
                          Tile.EAST, Tile.WEST, Tile.NORTH])
        self.assertIsNone(self.context.player().decision)

        # player 2 draws a CHAR7 and discards BAMBOO7
        self.context.state = 'discarding'
        draw_for_player(self.context, 2, last_player_idx=1, tile=Tile.CHAR7)
        self.context.player().decision = Tile.BAMBOO7
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'discarded')
        self.assertEqual(self.context.players[0].discarded, [])
        self.assertEqual(self.context.players[1].discarded, [Tile.CHAR8])
        self.assertEqual(self.context.players[2].discarded, [Tile.EAST, Tile.BAMBOO7])
        self.assertEqual(self.context.players[3].discarded, [])
        self.assertEqual(self.context.discarded_pool, [Tile.CHAR8, Tile.EAST, Tile.BAMBOO7])
        self.assertIsNone(self.context.player().hand.last_tile)
        self.assertEqual(self.context.player().hand.free_tiles,
                         [Tile.CHAR7, Tile.CHAR9, Tile.CIRCLE1,
                          Tile.CIRCLE2, Tile.CIRCLE3, Tile.BAMBOO5,
                          Tile.BAMBOO6, Tile.BAMBOO8, Tile.BAMBOO9,
                          Tile.BAMBOO9, Tile.EAST, Tile.WEST, Tile.NORTH])
        self.assertIsNone(self.context.player().decision)

        # test bot
        self.context.players[3].extra['bot'] = True
        self.context.state = 'discarding'
        draw_for_player(self.context, 3, last_player_idx=2, tile=Tile.SOUTH)
        self.context.player().decision = 'doesnt-matter-for-bot'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'discarded')
        self.assertEqual(self.context.players[0].discarded, [])
        self.assertEqual(self.context.players[1].discarded, [Tile.CHAR8])
        self.assertEqual(self.context.players[2].discarded, [Tile.EAST, Tile.BAMBOO7])
        self.assertEqual(self.context.players[3].discarded, [Tile.SOUTH])
        self.assertEqual(self.context.discarded_pool, [Tile.CHAR8, Tile.EAST, Tile.BAMBOO7, Tile.SOUTH])
        self.assertIsNone(self.context.player().hand.last_tile)
        self.assertEqual(self.context.player().hand.free_tiles,
                         [Tile.CHAR5, Tile.CHAR5, Tile.CHAR6,
                          Tile.CHAR7, Tile.CHAR8, Tile.CIRCLE3,
                          Tile.CIRCLE3, Tile.BAMBOO2, Tile.BAMBOO3,
                          Tile.BAMBOO4, Tile.BAMBOO6, Tile.BAMBOO7, Tile.BAMBOO8])
        self.assertIsNone(self.context.player().decision)

    def test_illegal_type(self):
        # test the case where player's decision is not a tile
        draw_for_player(self.context, 1, last_player_idx=0, tile=Tile.GREEN)
        self.context.player().decision = 'invalid-input'
        orig_context = self.context.clone()
        self.assertFalse(flow.next(self.context))
        self.assertEqual(self.context, orig_context)

    def test_illegal_tile(self):
        # test the case where player tries to discard a tile that he doesn't own
        draw_for_player(self.context, 1, last_player_idx=0, tile=Tile.GREEN)
        self.context.player().decision = Tile.WEST
        orig_context = self.context.clone()
        self.assertFalse(flow.next(self.context))
        self.assertEqual(self.context, orig_context)


class TestDiscardedHandler(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()
        self.context.state = 'discarded'
        self.context.wall = Wall()

        hands = [p.hand for p in self.context.players]

        hands[0].add_free_tiles([Tile.CHAR1])
        hands[1].add_free_tiles([Tile.CHAR2, Tile.CHAR4, Tile.CIRCLE1, Tile.CIRCLE1])
        hands[2].add_free_tiles([Tile.CHAR3, Tile.CHAR3, Tile.CHAR3, Tile.CHAR2])
        hands[3].add_free_tiles([Tile.CHAR4, Tile.CIRCLE4])

    def test_4_kong_viable_deicsions(self):
        self.context.settings.patterns_win.append('four-kongs')

        self.context.players[0].hand.free_tiles = [Tile.CHAR1, Tile.CHAR1, Tile.CHAR1, Tile.RED]
        self.context.players[0].hand.fixed_groups = [
            TileGroup([Tile.CHAR2] * 4, TileGroup.KONG_EXPOSED),
            TileGroup([Tile.CHAR3] * 4, TileGroup.KONG_EXPOSED),
            TileGroup([Tile.CHAR4] * 4, TileGroup.KONG_CONCEALED)
        ]

        self.context.players[2].hand.free_tiles = [Tile.GREEN, Tile.WHITE]
        draw_for_player(self.context, 2, tile=Tile.CHAR1)
        self.context.discard(Tile.CHAR1)

        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'melding')
        self.assertEqual(self.context.players[0].extra.get('viable_decisions'),
                         ['win', 'pong', 'skip'])

    def test_4_wind_tie(self):
        draw_for_player(self.context, 0, tile=Tile.EAST)
        draw_for_player(self.context, 1, tile=Tile.EAST)
        draw_for_player(self.context, 2, tile=Tile.EAST)
        self.context.discard(Tile.EAST, 0)
        self.context.discard(Tile.EAST, 1)
        self.context.discard(Tile.EAST, 2)

        draw_for_player(self.context, 3, last_player_idx=2, tile=Tile.EAST)
        self.context.discard(Tile.EAST, 3)

        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertFalse(self.context.winners)
        self.assertEqual(self.context.extra.get('tie_type'), '4-wind')

    def test_4_waiting_tie(self):
        draw_for_player(self.context, 3, last_player_idx=2, tile=Tile.EAST)
        self.context.discard(Tile.EAST)
        for player in self.context.players:
            player.extra['declared_ready'] = True

        orig_context = self.context.clone()

        # tie_on_4_waiting is off, should go to 'drawing'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'drawing')

        self.context = orig_context
        self.context.settings.tie_on_4_waiting = True

        # tie_on_4_waiting is on
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertFalse(self.context.winners)
        self.assertEqual(self.context.extra.get('tie_type'), '4-waiting')

    def test_declarable_off(self):
        self.context.settings.declarable = False
        draw_for_player(self.context, 0, last_player_idx=2, tile=Tile.CHAR3)
        self.context.discard(Tile.CHAR3)

        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'melding')
        self.assertEqual(self.context.cur_player_idx, 0)
        self.assertEqual(self.context.last_player_idx, 2)

    def test_declare_ready(self):
        draw_for_player(self.context, 0, last_player_idx=3, tile=Tile.EAST)
        self.context.discard(Tile.EAST)

        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [['declare', 'skip'], None, None, None])
        self.assertEqual(self.context.cur_player_idx, 0)
        self.assertEqual(self.context.last_player_idx, 3)
        self.assertFalse(self.context.player().extra.get('declared_ready'))

        self.context.players[0].decision = 'declare'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'discarded')
        self.assertEqual(self.context.cur_player_idx, 0)
        self.assertEqual(self.context.last_player_idx, 3)
        self.assertTrue(self.context.player().extra.get('declared_ready'))
        self.assertEqual(self.context.player().extra.get('waiting_tiles'),
                         [Tile.CHAR1])
        self.assertIsNone(self.context.players[0].decision)

        draw_for_player(self.context, 1, last_player_idx=0, tile=Tile.EAST)
        self.context.discard(Tile.EAST)
        self.context.players[1].decision = 'skip'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'discarded')

        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'drawing')
        self.assertEqual(self.context.cur_player_idx, 2)
        self.assertEqual(self.context.last_player_idx, 1)
        self.assertFalse(self.context.players[1].extra.get('declared_ready'))
        self.assertIsNone(self.context.players[1].decision)

    def test_someone_can_meld(self):
        draw_for_player(self.context, 0, last_player_idx=3, tile=Tile.CHAR3)
        self.context.discard(Tile.CHAR3)

        self.context.player().decision = 'skip'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'discarded')
        self.assertIsNone(self.context.player().decision)

        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'melding')

        viable_decisions = [player.extra.get('viable_decisions') for player in self.context.players]
        self.assertEqual(viable_decisions, [None, ['win', 'chow', 'skip'], ['kong', 'pong', 'skip'], None])

    def test_bad_context(self):
        self.assertFalse(flow.next(self.context))


class TestMeldingHandler(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()
        self.context.state = 'melding'
        self.context.wall = Wall()

        players = [p for p in self.context.players]
        hands = [p.hand for p in players]

        # lousy hand for player 0
        hands[0].add_free_tiles([Tile.CHAR2, Tile.CHAR4, Tile.CHAR9,
                                 Tile.CIRCLE9, Tile.BAMBOO1, Tile.BAMBOO4,
                                 Tile.EAST, Tile.SOUTH, Tile.WEST,
                                 Tile.NORTH, Tile.RED, Tile.GREEN, Tile.GREEN])
        # ready hand for player 1 - waiting for CHAR6 and CHAR9
        hands[1].add_free_tiles([Tile.CHAR2, Tile.CHAR2, Tile.CHAR7,
                                 Tile.CHAR8, Tile.BAMBOO2, Tile.BAMBOO3,
                                 Tile.BAMBOO4, Tile.SOUTH, Tile.SOUTH,
                                 Tile.SOUTH, Tile.WHITE, Tile.WHITE, Tile.WHITE])
        # lousy hand for player 2
        hands[2].add_free_tiles([Tile.CIRCLE1, Tile.CHAR6, Tile.CHAR6,
                                 Tile.BAMBOO5, Tile.BAMBOO6, Tile.BAMBOO7,
                                 Tile.BAMBOO8, Tile.BAMBOO9, Tile.BAMBOO9,
                                 Tile.EAST, Tile.EAST, Tile.WEST, Tile.NORTH])
        # ready hand for player 3 - waiting for CHAR5 and CIRCLE3
        hands[3].add_free_tiles([Tile.CHAR5, Tile.CHAR5, Tile.CHAR6,
                                 Tile.CHAR7, Tile.CHAR8, Tile.CIRCLE3,
                                 Tile.CIRCLE3, Tile.BAMBOO2, Tile.BAMBOO3,
                                 Tile.BAMBOO4, Tile.BAMBOO6, Tile.BAMBOO7, Tile.BAMBOO8])

        draw_for_player(self.context, 0, tile=Tile.CHAR6)
        self.context.discard(Tile.CHAR6)

        players[1].extra['viable_decisions'] = ['win', 'chow', 'skip']
        players[2].extra['viable_decisions'] = ['pong', 'skip']

    def test_skip(self):
        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [None, ['win', 'chow', 'skip'], ['pong', 'skip'], None])

        self.context.players[1].decision = 'skip'
        result = flow.next(self.context)
        self.assertFalse(result)

        self.context.players[2].decision = 'skip'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'drawing')
        self.assertEqual(self.context.cur_player_idx, 1)
        self.assertEqual(self.context.last_player_idx, 0)
        self.assertEqual(self.context.discarded_pool, [Tile.CHAR6])

        self.assertEqual(self.context.extra, {})
        self.assertEqual(self.context.players[0].extra, {})
        self.assertEqual(self.context.players[1].extra, { 'water': [Tile.CHAR6, Tile.CHAR9] })
        self.assertEqual(self.context.players[2].extra, {})
        self.assertEqual(self.context.players[3].extra, {})

        self.assertIsNone(self.context.players[0].decision)
        self.assertIsNone(self.context.players[1].decision)
        self.assertIsNone(self.context.players[2].decision)
        self.assertIsNone(self.context.players[3].decision)

    def test_tie(self):
        self.context.settings.tie_on_4_kongs = True

        # already 3 kongs on the table
        kong_group = TileGroup([Tile.RED] * 4, TileGroup.KONG_EXPOSED)
        self.context.players[0].hand.fixed_groups.append(kong_group)
        self.context.players[1].hand.fixed_groups.append(kong_group)
        self.context.players[2].hand.fixed_groups.append(kong_group)

        # player 3 draws and discards a WHITE
        draw_for_player(self.context, 3, tile=Tile.WHITE)
        self.context.discard(Tile.WHITE)
        self.context.players[1].extra['viable_decisions'] = ['kong', 'pong', 'skip']
        del self.context.players[2].extra['viable_decisions']

        # cannot go to next state because player 1 hasn't make a decision
        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions,
                         [None, ['kong', 'pong', 'skip'], None, None])

        # player 1 decides to kong -> 4-kong tie
        self.context.players[1].decision = 'kong'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertFalse(self.context.winners)
        self.assertEqual(self.context.extra.get('tie_type'), '4-kong')

        # viable_decisions in player.extra should be cleaned up afterward
        self.assertFalse(self.context.players[1].extra.get('viable_decisions'))
        self.assertIsNone(self.context.players[1].decision)

    def test_single_win(self):
        self.context.players[1].decision = 'win'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertEqual(self.context.winners, [1])
        self.assertEqual(self.context.players[1].extra.get('win_type'), 'melded')
        self.assertEqual(self.context.players[1].extra.get('chucker'), 0)

        # viable_decisions in player.extra should be cleaned up afterward
        self.assertFalse(self.context.players[1].extra.get('viable_decisions'))
        self.assertIsNone(self.context.players[1].decision)

    def test_win_bot(self):
        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions, [None, ['win', 'chow', 'skip'], ['pong', 'skip'], None])

        self.context.players[1].extra['bot'] = True
        self.context.players[2].extra['bot'] = True

        # bot chooses to win for player 1
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertEqual(self.context.winners, [1])
        self.assertEqual(self.context.players[1].extra.get('chucker'), 0)

        # viable_decisions in player.extra should be cleaned up afterward
        self.assertFalse(self.context.players[1].extra.get('viable_decisions'))
        self.assertFalse(self.context.players[2].extra.get('viable_decisions'))
        self.assertIsNone(self.context.players[1].decision)
        self.assertIsNone(self.context.players[2].decision)

    def test_single_win_prority(self):
        # player 1~3 all wait for CHAR8
        self.context.players[1].hand.free_tiles = [Tile.CHAR8]
        self.context.players[2].hand.free_tiles = [Tile.CHAR8]
        self.context.players[3].hand.free_tiles = [Tile.CHAR8]
        self.context.players[1].extra['viable_decisions'] = ['win', 'skip']
        self.context.players[2].extra['viable_decisions'] = ['win', 'skip']
        self.context.players[3].extra['viable_decisions'] = ['win', 'skip']

        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions,
                         [None, ['win', 'skip'], ['win', 'skip'], ['win', 'skip']])

        # player 3 decides to win
        self.context.players[3].decision = 'win'

        # still have to wait for player 1
        self.assertFalse(flow.next(self.context))

        # player 1 decides to skip
        self.context.players[1].decision = 'skip'

        # still have to wait for player 2
        self.assertFalse(flow.next(self.context))

        # player 2 decides to win
        self.context.players[2].decision = 'win'

        # final winner: player 2
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertEqual(self.context.winners, [2])
        self.assertEqual(self.context.players[2].extra.get('win_type'), 'melded')
        self.assertEqual(self.context.players[2].extra.get('chucker'), 0)

        # viable_decisions in player.extra should be cleaned up afterward
        self.assertFalse(self.context.players[1].extra.get('viable_decisions'))
        self.assertFalse(self.context.players[2].extra.get('viable_decisions'))
        self.assertFalse(self.context.players[3].extra.get('viable_decisions'))
        self.assertIsNone(self.context.players[1].decision)
        self.assertIsNone(self.context.players[2].decision)
        self.assertIsNone(self.context.players[3].decision)

    def test_multi_wins(self):
        self.context.settings.multi_winners = True

        # player 1~3 all wait for CHAR8
        self.context.players[1].hand.free_tiles = [Tile.CHAR8]
        self.context.players[2].hand.free_tiles = [Tile.CHAR8]
        self.context.players[3].hand.free_tiles = [Tile.CHAR8]
        self.context.players[1].extra['viable_decisions'] = ['win', 'skip']
        self.context.players[2].extra['viable_decisions'] = ['win', 'skip']
        self.context.players[3].extra['viable_decisions'] = ['win', 'skip']

        # player 0 discards a CHAR8
        draw_for_player(self.context, 0, last_player_idx=3, tile=Tile.CHAR8)
        self.context.discard(Tile.CHAR8)

        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions,
                         [None, ['win', 'skip'], ['win', 'skip'], ['win', 'skip']])

        # player 1 and 3 decide to win
        self.context.players[1].decision = 'win'
        self.context.players[3].decision = 'win'

        # still have to wait for player 2
        result = flow.next(self.context)
        self.assertFalse(result)

        # player 1 and 3 decide to win, player 2 skips
        self.context.players[2].decision = 'skip'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertEqual(self.context.winners, [1, 3])
        self.assertEqual(self.context.players[1].extra.get('win_type'), 'melded')
        self.assertEqual(self.context.players[1].extra.get('chucker'), 0)
        self.assertEqual(self.context.players[3].extra.get('win_type'), 'melded')
        self.assertEqual(self.context.players[3].extra.get('chucker'), 0)

        # viable_decisions in player.extra should be cleaned up afterward
        self.assertFalse(self.context.players[1].extra.get('viable_decisions'))
        self.assertFalse(self.context.players[2].extra.get('viable_decisions'))
        self.assertFalse(self.context.players[3].extra.get('viable_decisions'))
        self.assertIsNone(self.context.players[1].decision)
        self.assertIsNone(self.context.players[2].decision)
        self.assertIsNone(self.context.players[3].decision)

    def test_kong(self):
        draw_for_player(self.context, 3, tile=Tile.WHITE)
        self.context.discard(Tile.WHITE)

        self.context.players[1].extra['viable_decisions'] = ['kong', 'pong', 'skip']
        del self.context.players[2].extra['viable_decisions']

        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions,
                         [None, ['kong', 'pong', 'skip'], None, None])

        self.context.players[1].decision = 'kong'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'drawing')
        self.assertEqual(self.context.cur_player_idx, 1)
        self.assertEqual(self.context.last_player_idx, 3)
        self.assertEqual(self.context.players[1].hand.fixed_groups,
                         [TileGroup([Tile.WHITE] * 4, TileGroup.KONG_EXPOSED)])
        self.assertEqual(self.context.players[1].hand.free_tiles,
                         [Tile.CHAR2, Tile.CHAR2, Tile.CHAR7, Tile.CHAR8,
                          Tile.BAMBOO2, Tile.BAMBOO3, Tile.BAMBOO4, Tile.SOUTH,
                          Tile.SOUTH, Tile.SOUTH])

        self.assert_cleaned(self.context)

    def test_pong(self):
        self.context.players[1].decision = 'chow'
        self.context.players[2].decision = 'pong'

        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'discarding')
        self.assertEqual(self.context.cur_player_idx, 2)
        self.assertEqual(self.context.last_player_idx, 0)
        self.assertEqual(self.context.players[2].hand.fixed_groups,
                         [TileGroup([Tile.CHAR6] * 3, TileGroup.PONG)])
        self.assertEqual(self.context.players[2].hand.free_tiles,
                         [Tile.CIRCLE1, Tile.BAMBOO5, Tile.BAMBOO6, Tile.BAMBOO7,
                          Tile.BAMBOO8, Tile.BAMBOO9, Tile.BAMBOO9, Tile.EAST,
                          Tile.EAST, Tile.WEST, Tile.NORTH])

        self.assertEqual(self.context.extra, {})
        self.assertEqual(self.context.players[0].extra, {})
        self.assertEqual(self.context.players[1].extra, { 'water': [Tile.CHAR6, Tile.CHAR9] })
        self.assertEqual(self.context.players[2].extra, {})
        self.assertEqual(self.context.players[3].extra, {})

        self.assertIsNone(self.context.players[0].decision)
        self.assertIsNone(self.context.players[1].decision)
        self.assertIsNone(self.context.players[2].decision)
        self.assertIsNone(self.context.players[3].decision)

    def test_bot_skips_melding(self):
        # dumb bot doesn't kong, pong, nor chow
        self.context.players[1].extra['bot'] = True
        self.context.players[2].extra['bot'] = True

        self.context.players[1].extra['viable_decisions'] = ['chow', 'skip']
        self.context.players[2].extra['viable_decisions'] = ['kong', 'pong', 'skip']

        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'drawing')
        self.assertEqual(self.context.cur_player_idx, 1)
        self.assertEqual(self.context.last_player_idx, 0)

        # viable_decisions in player.extra should be cleaned up afterward
        self.assertFalse(self.context.players[1].extra.get('viable_decisions'))
        self.assertFalse(self.context.players[2].extra.get('viable_decisions'))
        self.assertIsNone(self.context.players[1].decision)
        self.assertIsNone(self.context.players[2].decision)

    def test_declared_ready_melding(self):
        # after a player declared, he doesn't kong, pong, nor chow
        self.context.players[1].extra['declared_ready'] = True
        self.context.players[2].extra['declared_ready'] = True

        self.context.players[1].extra['viable_decisions'] = ['chow', 'skip']
        self.context.players[2].extra['viable_decisions'] = ['kong', 'pong', 'skip']

        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'drawing')
        self.assertEqual(self.context.cur_player_idx, 1)
        self.assertEqual(self.context.last_player_idx, 0)

        # viable_decisions in player.extra should be cleaned up afterward
        self.assertFalse(self.context.players[1].extra.get('viable_decisions'))
        self.assertFalse(self.context.players[2].extra.get('viable_decisions'))

    def test_declared_ready_winning(self):
        # after a player declared, he can only win
        self.context.settings.multi_winners = True

        self.context.players[1].extra['declared_ready'] = True
        self.context.players[2].extra['declared_ready'] = True
        self.context.players[1].extra['waiting_tiles'] = [Tile.CHAR6]
        self.context.players[2].extra['waiting_tiles'] = [Tile.CHAR6]

        self.context.players[1].extra['viable_decisions'] = ['win', 'chow', 'skip']
        self.context.players[2].extra['viable_decisions'] = ['win', 'pong', 'skip']

        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'end')
        self.assertEqual(self.context.winners, [1, 2])
        self.assertEqual(self.context.players[1].extra.get('chucker'), 0)
        self.assertEqual(self.context.players[2].extra.get('chucker'), 0)

        # viable_decisions in player.extra should be cleaned up afterward
        self.assertFalse(self.context.players[1].extra.get('viable_decisions'))
        self.assertFalse(self.context.players[2].extra.get('viable_decisions'))
        self.assertIsNone(self.context.players[1].decision)
        self.assertIsNone(self.context.players[2].decision)

    def test_single_chow(self):
        self.context.players[1].decision = 'chow'
        self.context.players[2].decision = 'skip'
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'discarding')
        self.assertEqual(self.context.cur_player_idx, 1)
        self.assertEqual(self.context.last_player_idx, 0)
        self.assertEqual(self.context.discarded_pool, [])
        self.assertEqual(self.context.players[1].hand.fixed_groups,
                         [TileGroup([Tile.CHAR6, Tile.CHAR7, Tile.CHAR8], TileGroup.CHOW)])
        self.assertEqual(self.context.players[1].hand.free_tiles,
                         [Tile.CHAR2, Tile.CHAR2, Tile.BAMBOO2, Tile.BAMBOO3,
                          Tile.BAMBOO4, Tile.SOUTH, Tile.SOUTH, Tile.SOUTH,
                          Tile.WHITE, Tile.WHITE, Tile.WHITE])

        self.assertEqual(self.context.extra, {})
        self.assertEqual(self.context.players[0].extra, {})
        self.assertEqual(self.context.players[1].extra, { 'water': [Tile.CHAR6, Tile.CHAR9] })
        self.assertEqual(self.context.players[2].extra, {})
        self.assertEqual(self.context.players[3].extra, {})

        self.assertIsNone(self.context.players[0].decision)
        self.assertIsNone(self.context.players[1].decision)
        self.assertIsNone(self.context.players[2].decision)
        self.assertIsNone(self.context.players[3].decision)

    def test_multi_chow(self):
        draw_for_player(self.context, 1, last_player_idx=0, tile=Tile.BAMBOO6)
        self.context.discard(Tile.BAMBOO6)
        del self.context.players[1].extra['viable_decisions']
        self.context.players[2].extra['viable_decisions'] = ['chow', 'skip']
        self.context.players[2].decision = 'chow'

        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'chowing')
        self.assertEqual(self.context.cur_player_idx, 2)
        self.assertEqual(self.context.last_player_idx, 1)
        self.assertEqual(self.context.player().extra.get('chow_combs'),
                         [(Tile.BAMBOO5, Tile.BAMBOO7), (Tile.BAMBOO7, Tile.BAMBOO8)])

        # viable_decisions in player.extra should be cleaned up afterward
        self.assertFalse(self.context.players[1].extra.get('viable_decisions'))
        self.assertFalse(self.context.players[2].extra.get('viable_decisions'))
        self.assertIsNone(self.context.players[1].decision)
        self.assertIsNone(self.context.players[2].decision)

    def test_bad_context(self):
        del self.context.discarded_pool[:]
        self.assertFalse(flow.next(self.context))

        self.context.discarded_pool.append(Tile.RED)
        self.assertFalse(flow.next(self.context))

        self.context.discarded_pool[0] = Tile.CHAR6
        del self.context.players[1].extra['viable_decisions']
        del self.context.players[2].extra['viable_decisions']
        self.assertFalse(flow.next(self.context))

    def assert_cleaned(self, context):
        # check if the context is cleaned up
        self.assertEqual(self.context.extra, {})
        self.assertEqual(self.context.players[0].extra, {})
        self.assertEqual(self.context.players[1].extra, {})
        self.assertEqual(self.context.players[2].extra, {})
        self.assertEqual(self.context.players[3].extra, {})

        self.assertIsNone(self.context.players[0].decision)
        self.assertIsNone(self.context.players[1].decision)
        self.assertIsNone(self.context.players[2].decision)
        self.assertIsNone(self.context.players[3].decision)


class TestChowingHandler(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()
        self.context.state = 'melding'
        self.context.wall = Wall()

        hands = [player.hand for player in self.context.players]

        hands[0].add_free_tiles([Tile.CHAR1, Tile.CHAR2, Tile.CHAR3,
                                 Tile.CHAR1, Tile.CHAR2, Tile.CHAR3,
                                 Tile.CHAR4, Tile.CHAR5, Tile.CHAR6])
        hands[1].add_free_tiles([Tile.CIRCLE1, Tile.CIRCLE2, Tile.CIRCLE3,
                                 Tile.CIRCLE4, Tile.CIRCLE5, Tile.CIRCLE6])
        hands[2].add_free_tiles([Tile.BAMBOO1, Tile.BAMBOO2, Tile.BAMBOO3,
                                 Tile.BAMBOO4, Tile.BAMBOO5, Tile.BAMBOO6])
        hands[3].add_free_tiles([Tile.CHAR4, Tile.CHAR5, Tile.CHAR6,
                                 Tile.CHAR7, Tile.CHAR8, Tile.CHAR9])

        draw_for_player(self.context, 3, last_player_idx=2, tile=Tile.CHAR3)
        self.context.discard(Tile.CHAR3)
        self.context.players[0].extra['viable_decisions'] = ['pong', 'chow', 'skip']

        self.context.players[0].decision = 'chow'
        flow.next(self.context)

    def test_multi_chow(self):
        self.assertEqual(self.context.state, 'chowing')

        result = flow.next(self.context)
        self.assertFalse(result)
        self.assertEqual(result.viable_decisions,
                         [[(Tile.CHAR1, Tile.CHAR2), (Tile.CHAR2, Tile.CHAR4), (Tile.CHAR4, Tile.CHAR5)],
                          None, None, None])

        # invalid decision
        self.context.players[0].decision = (Tile.CHAR2, Tile.CHAR3)
        self.assertFalse(flow.next(self.context))

        # chow CHAR2 CHAR3 CHAR4
        self.context.players[0].decision = (Tile.CHAR2, Tile.CHAR4)
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'discarding')
        self.assertEqual(self.context.cur_player_idx, 0)
        self.assertEqual(self.context.last_player_idx, 3)
        self.assertEqual(self.context.player().hand.fixed_groups,
                         [TileGroup([Tile.CHAR2, Tile.CHAR3, Tile.CHAR4], TileGroup.CHOW)])
        self.assertEqual(self.context.player().hand.free_tiles,
                         [Tile.CHAR1, Tile.CHAR1, Tile.CHAR2, Tile.CHAR3,
                          Tile.CHAR3, Tile.CHAR5, Tile.CHAR6])

    def test_bad_context(self):
        orig_context = self.context.clone()

        del self.context.discarded_pool[:]
        self.assertFalse(flow.next(self.context))

        self.context = orig_context.clone()
        del self.context.player().extra['chow_combs']
        self.assertFalse(flow.next(self.context))

        self.context = orig_context
        self.context.player(-1).discarded[0] = Tile.RED
        self.assertFalse(flow.next(self.context))


class TestEndHandler(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()
        self.context.state = 'end'
        self.context.wall = Wall()

        hands = [player.hand for player in self.context.players]

        hands[0].add_free_tiles([Tile.CHAR1])
        hands[1].add_free_tiles([Tile.CHAR2])
        hands[2].add_free_tiles([Tile.CHAR3])
        hands[3].add_free_tiles([Tile.CHAR4])

        draw_for_player(self.context, 0, last_player_idx=2, tile=Tile.CHAR1)
        self.context.winners = [0]
        self.context.players[0].extra['win_type'] = 'self-picked'

    def test_score(self):
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'scored')

        match_result = MatchResult((1, 2, 3), multiplier=1)

        self.assertEqual(self.context.players[0].extra.get('patterns_matched'), {
            'all-pongs': match_result,
            'heaven-win': match_result,
            'same-suit': match_result,
            'waiting-for-one': MatchResult((1, 2, 3), multiplier=1, extra='eye')
        })

    # TODO: more tests...

    def test_bad_context(self):
        orig_context = self.context.clone()

        del self.context.players[0].extra['win_type']
        self.assertFalse(flow.next(self.context))

        self.context = orig_context
        self.context.winners = None
        self.assertFalse(flow.next(self.context))


class TestScoredHandler(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()
        self.context.state = 'scored'
        self.context.wall = Wall()

        # deal some tiles
        for player in self.context.players:
            hand = player.hand
            for __ in xrange(13):
                tile = self.context.wall.draw()
                hand.add_free_tile(tile)

    def test_round0_match0_dealer0_winner0(self):
        self.context.round = 0
        self.context.match = 0
        self.context.dealer = 0
        self.context.winners = [0]
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'start')
        self.assert_empty_hands(self.context)
        self.assertEqual(self.context.round, 0)
        self.assertEqual(self.context.match, 1)
        self.assertEqual(self.context.dealer, 0)
        self.assertEqual(self.context.dealer_defended, 1)

    def test_round1_match3_dealer0_winner2(self):
        self.context.round = 1
        self.context.match = 3
        self.context.dealer = 0
        self.context.winners = [2]
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'start')
        self.assert_empty_hands(self.context)
        self.assertEqual(self.context.round, 1)
        self.assertEqual(self.context.match, 4)
        self.assertEqual(self.context.dealer, 1)
        self.assertEqual(self.context.dealer_defended, 0)

    def test_round2_match4_dealer0_no_winner(self):
        self.context.round = 2
        self.context.match = 4
        self.context.dealer = 0
        self.context.winners = None
        self.context.dealer_defended = 2
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'start')
        self.assert_empty_hands(self.context)
        self.assertEqual(self.context.round, 2)
        self.assertEqual(self.context.match, 5)
        self.assertEqual(self.context.dealer, 0)
        self.assertEqual(self.context.dealer_defended, 3)

    def test_round1_match5_dealer3_winner1_2(self):
        self.context.round = 1
        self.context.match = 5
        self.context.dealer = 3
        self.context.winners = [1, 2]
        self.context.dealer_defended = 1
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'start')
        self.assert_empty_hands(self.context)
        self.assertEqual(self.context.round, 2)
        self.assertEqual(self.context.match, 0)
        self.assertEqual(self.context.dealer, 0)
        self.assertEqual(self.context.dealer_defended, 0)

    def test_round0_match8_dealer3_no_winner(self):
        self.context.round = 0
        self.context.match = 8
        self.context.dealer = 3
        self.context.winners = None
        self.context.dealer_defended = 3
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'start')
        self.assert_empty_hands(self.context)
        self.assertEqual(self.context.round, 0)
        self.assertEqual(self.context.match, 9)
        self.assertEqual(self.context.dealer, 3)
        self.assertEqual(self.context.dealer_defended, 4)

    def test_max_dealer_defended(self):
        self.context.settings.max_dealer_defended = 3
        self.context.round = 1
        self.context.match = 2
        self.context.dealer = 2
        self.context.winners = None
        self.context.dealer_defended = 3
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'start')
        self.assert_empty_hands(self.context)
        self.assertEqual(self.context.round, 1)
        self.assertEqual(self.context.match, 3)
        self.assertEqual(self.context.dealer, 3)
        self.assertEqual(self.context.dealer_defended, 0)

    def test_max_dealer_defended2(self):
        self.context.settings.max_dealer_defended = 3
        self.context.round = 1
        self.context.match = 2
        self.context.dealer = 2
        self.context.winners = [2]
        self.context.dealer_defended = 2
        self.assertTrue(flow.next(self.context))
        self.assertEqual(self.context.state, 'start')
        self.assert_empty_hands(self.context)
        self.assertEqual(self.context.round, 1)
        self.assertEqual(self.context.match, 3)
        self.assertEqual(self.context.dealer, 2)
        self.assertEqual(self.context.dealer_defended, 3)

    def assert_empty_hands(self, context):
        empty_hand = Hand()
        self.assertEqual(context.players[0].hand, empty_hand)
        self.assertEqual(context.players[1].hand, empty_hand)
        self.assertEqual(context.players[2].hand, empty_hand)
        self.assertEqual(context.players[3].hand, empty_hand)
        self.assertEqual(context.players[0].discarded, [])
        self.assertEqual(context.players[1].discarded, [])
        self.assertEqual(context.players[2].discarded, [])
        self.assertEqual(context.players[3].discarded, [])
        self.assertEqual(context.players[0].extra, {})
        self.assertEqual(context.players[1].extra, {})
        self.assertEqual(context.players[2].extra, {})
        self.assertEqual(context.players[3].extra, {})
        self.assertEqual(context.cur_player_idx, 0)
        self.assertIsNone(context.last_player_idx)
        self.assertIsNone(context.last_discarded())
        self.assertFalse(context.winners)
        self.assertIsNone(context.player().decision)
        self.assertEqual(context.extra, {})


#-----------------------------------------------------------------------------
# Utility functions
#-----------------------------------------------------------------------------

def draw_for_player(context, player_idx, last_player_idx=None, tile=None):
    context.last_player_idx = last_player_idx
    context.cur_player_idx = player_idx
    hand = context.player().hand
    tile_from_wall = context.wall.draw()
    hand.last_tile = tile or tile_from_wall
