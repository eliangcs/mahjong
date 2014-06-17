import unittest

from mahjong import patterns
from mahjong.patterns import MatchResult
from mahjong.types import GameContext, Tile, TileGroup, Wall


class TestModulePublicFunc(unittest.TestCase):

    def test_get(self):
        dealer_pattern = patterns.get('dealer')
        self.assertTrue(isinstance(dealer_pattern, patterns.Dealer))

        with self.assertRaises(KeyError):
            patterns.get('invalid-pattern-name')

    def test_match(self):
        context = GameContext()
        context.cur_player_idx = None
        with self.assertRaises(ValueError):
            patterns.match('dealer', context)

        context.cur_player_idx = 0
        with self.assertRaises(ValueError):
            patterns.match('dealer', context)


class TestMatchAll(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()
        self.context.wall = Wall()

    def test_four_flowers(self):
        self.context.settings.patterns_score = {
            'flower-seat': 1,
            'four-flowers': 2
        }
        self.context.players[0].hand.add_free_tiles([
            Tile.CHAR2, Tile.CHAR3, Tile.BAMBOO1, Tile.BAMBOO1
        ])

        # player got four special flowers
        self.context.players[0].hand.flowers = Tile.FLOWERS[0:4]
        self.context.players[0].hand.last_tile = Tile.CHAR4

        self.assertEqual(patterns.match_all(self.context, 0), {
            'four-flowers': MatchResult((1, 2, 3), 1, extra=['flowers'])
        })

        # player got four special flowers and a season of his seat (SPRING)
        self.context.players[0].hand.add_flower(Tile.SPRING)
        self.assertEqual(patterns.match_all(self.context, 0), {
            'flower-seat': MatchResult((1, 2, 3), 1, extra=[Tile.SPRING]),
            'four-flowers': MatchResult((1, 2, 3), 1, extra=['flowers'])
        })

        # player got all eight general flowers
        self.context.players[0].hand.flowers += Tile.FLOWERS[5:8]
        self.assertEqual(patterns.match_all(self.context, 0), {
            'four-flowers': MatchResult((1, 2, 3), 2, extra=['flowers', 'seasons'])
        })

        # player got four seaons and a special flower of his seat (PLUM)
        self.context.players[0].hand.flowers = Tile.FLOWERS[0:1] + Tile.FLOWERS[3:8]
        self.assertEqual(patterns.match_all(self.context, 0), {
            'flower-seat': MatchResult((1, 2, 3), 1, extra=[Tile.PLUM]),
            'four-flowers': MatchResult((1, 2, 3), 1, extra=['seasons'])
        })

    def test_concealed_triplets(self):
        self.context.settings.patterns_score = {
            'three-concealed-triplets': 2,
            'four-concealed-triplets': 5,
            'five-concealed-triplets': 8
        }

        # wait for CHAR4 and CIRCLE5
        self.context.players[1].hand.add_free_tiles([
            Tile.CHAR3, Tile.CHAR4, Tile.CHAR4, Tile.CHAR4, Tile.CHAR5,
            Tile.CIRCLE5, Tile.CIRCLE5,
            Tile.BAMBOO3, Tile.BAMBOO3, Tile.BAMBOO3
        ])
        self.context.players[1].hand.fixed_groups += [
            TileGroup([Tile.BAMBOO5] * 4, TileGroup.KONG_CONCEALED)
        ]

        match_result = MatchResult((0, 2, 3), 1)

        self.context.players[1].hand.last_tile = Tile.CHAR4
        self.assertEqual(patterns.match_all(self.context, 1), {
            'three-concealed-triplets': match_result
        })

        # CIRCLE5 discarded by others is not concealed
        self.context.players[1].hand.move_last_tile()
        self.context.discarded_pool.append(Tile.CIRCLE5)
        self.assertEqual(patterns.match_all(self.context, 1), {
            'three-concealed-triplets': match_result
        })

        # CIRCLE5 drawn by player himself is concealed
        self.context.players[1].hand.last_tile = Tile.CIRCLE5
        self.assertEqual(patterns.match_all(self.context, 1), {
            'four-concealed-triplets': match_result
        })

        # add another concealed kong, making it five concealed triplets
        self.context.players[1].hand.fixed_groups += [
            TileGroup([Tile.EAST] * 4, TileGroup.KONG_CONCEALED)
        ]
        self.assertEqual(patterns.match_all(self.context, 1), {
            'five-concealed-triplets': match_result
        })

    def test_flower_win_after_dealing(self):
        self.context.settings.patterns_score = {
            'self-picked': 1,
            'purely-concealed': 1,
            'dealer': 1,
            'dealer-defended': 2,
            'konged-or-flowered': 1,
            'flower-seat': 1,
            'four-flowers': 2,
            'purely-concealed-self-picked': 3,
            'flower-win-after-dealing': 4,
            'seven-flowers': 8,
            'eight-flowers': 8,
            'earth-win': 16,
            'heaven-win': 24
        }

        self.context.dealer = 3
        self.context.dealer_defended = 3

        # flower win but not a winning hand
        self.context.players[2].hand.flowers = Tile.FLOWERS[0:8]
        self.context.players[2].hand.add_free_tiles([
            Tile.CHAR1, Tile.CHAR3, Tile.CHAR5, Tile.GREEN
        ])
        self.context.players[2].extra.update({
            'win_type': 'flower-won'
        })
        self.context.extra['flower_chucker'] = 3

        self.context.players[2].hand.last_tile = Tile.WHITE

        self.assertEqual(patterns.match_all(self.context, 2), {
            'dealer': MatchResult(3, 1),
            'dealer-defended': MatchResult(3, 3),
            'seven-flowers': MatchResult(3, 1),
            'flower-win-after-dealing': MatchResult(3, 1)
        })

        # flower win and a winning hand
        self.context.players[2].hand.free_tiles = [
            Tile.CHAR1, Tile.CHAR2, Tile.CHAR3, Tile.GREEN
        ]
        self.context.players[2].extra.update({
            'win_type': 'self-picked',
            'flowered': True
        })
        self.context.players[2].hand.last_tile = Tile.GREEN

        self.assertEqual(patterns.match_all(self.context, 2), {
            'dealer': MatchResult(3, 1),
            'dealer-defended': MatchResult(3, 3),
            'seven-flowers': MatchResult(3, 1),
            'flower-win-after-dealing': MatchResult(3, 1),
            'earth-win': MatchResult((0, 1, 3), 1),
            'four-flowers': MatchResult((0, 1), 2, extra=['flowers', 'seasons']),
            'konged-or-flowered': MatchResult((0, 1, 3), 1)
        })

        # eliminate earth-win
        self.context.discard(Tile.GREEN, player_idx=2)
        self.context.players[2].hand.add_free_tile(Tile.RED)
        self.context.players[2].hand.last_tile = Tile.RED

        self.assertEqual(patterns.match_all(self.context, 2), {
            'dealer': MatchResult(3, 1),
            'dealer-defended': MatchResult(3, 3),
            'seven-flowers': MatchResult(3, 1),
            'four-flowers': MatchResult((0, 1), 2, extra=['flowers', 'seasons']),
            'konged-or-flowered': MatchResult((0, 1, 3), 1),
            'purely-concealed-self-picked': MatchResult((0, 1, 3), 1)
        })

    def test_heaven_earth_human_win_ready(self):
        self.context.settings.patterns_score = {
            'dealer': 1,
            'dealer-defended': 2,
            'konged-or-flowered': 1,
            'declared-ready': 1,
            'self-picked': 1,
            'purely-concealed': 1,
            'purely-concealed-self-picked': 3,
            'earth-ready': 4,
            'heaven-ready': 8,
            'human-win': 8,
            'earth-win': 16,
            'heaven-win': 24
        }

        self.context.dealer = 3
        self.context.dealer_defended = 5

        # dealer kongs on his first drawing
        # and wins on the second drawing -- heaven-win
        self.context.players[3].hand.add_free_tiles([
            Tile.CIRCLE1, Tile.CIRCLE2, Tile.CIRCLE3, Tile.EAST
        ])
        self.context.players[3].hand.last_tile = Tile.EAST
        self.context.players[3].extra.update({
            'win_type': 'self-picked',
            'konged': True
        })

        self.assertEqual(patterns.match_all(self.context, 3), {
            'dealer-defended': MatchResult((0, 1, 2), 5),
            'konged-or-flowered': MatchResult((0, 1, 2), 1),
            'heaven-win': MatchResult((0, 1, 2), 1),
        })

        # non-dealer does the same -- earth-win
        self.context.dealer = 0
        self.assertEqual(patterns.match_all(self.context, 3), {
            'dealer': MatchResult(0, 1),
            'dealer-defended': MatchResult(0, 5),
            'konged-or-flowered': MatchResult((0, 1, 2), 1),
            'earth-win': MatchResult((0, 1, 2), 1),
        })

        # win on someone's first discarded tile -- human-win
        self.context.players[3].extra.update({
            'win_type': 'melded',
            'chucker': 0,
            'konged': None
        })
        self.context.players[3].hand.last_tile = None
        self.context.players[0].hand.last_tile = Tile.EAST
        self.context.discard(Tile.EAST, 0)

        self.assertEqual(patterns.match_all(self.context, 3), {
            'dealer': MatchResult(0, 1),
            'dealer-defended': MatchResult(0, 5),
            'human-win': MatchResult(0, 1),
            'purely-concealed': MatchResult(0, 1)
        })

        # dealer declared ready immediate after discarding his first tile
        # and wins on player 0's discarded tile -- heaven-ready
        self.context.dealer = 3
        self.context.players[3].extra.update({
            'immediate_ready': True,
            'declared_ready': True
        })

        # discard some tiles
        self.context.players[0].hand.add_free_tiles([Tile.EAST, Tile.WEST])
        self.context.players[3].hand.add_free_tiles([Tile.CHAR1, Tile.CHAR6])
        self.context.discard(Tile.CHAR1, 3)
        self.context.discard(Tile.CHAR6, 3)
        self.context.discard(Tile.WEST, 0)
        self.context.discard(Tile.EAST, 0)

        self.assertEqual(patterns.match_all(self.context, 3), {
            'dealer-defended': MatchResult(0, 5),
            'heaven-ready': MatchResult(0, 1),
            'purely-concealed': MatchResult(0, 1)
        })

        # non-dealer player ready immediate after discarding his first tile
        # and wins by self-picking -- earth-ready
        self.context.dealer = 0
        self.context.players[3].extra.update({
            'win_type': 'self-picked',
            'chucker': None
        })
        self.context.players[3].hand.last_tile = Tile.EAST

        # make it not purely-concealed
        self.context.players[3].hand.fixed_groups += [
            TileGroup([Tile.CHAR5] * 3, TileGroup.PONG)
        ]

        self.assertEqual(patterns.match_all(self.context, 3), {
            'dealer': MatchResult(0, 1),
            'dealer-defended': MatchResult(0, 5),
            'earth-ready': MatchResult((0, 1, 2), 1),
            'self-picked': MatchResult((0, 1, 2), 1)
        })

    def test_honor_patterns(self):
        self.context.settings.patterns_score = {
            'wind-seat': 1,
            'wind-round': 1,
            'dragons': 1,
            'all-pongs': 4,
            'mix-a-suit': 4,
            'small-three-dragons': 4,
            'all-honors': 8,
            'big-three-dragons': 8,
            'small-four-winds': 8,
            'big-four-winds': 16
        }

        # south round
        self.context.round = 1

        # big-four-winds
        self.context.players[0].hand.add_free_tiles([
            Tile.EAST, Tile.EAST, Tile.EAST,
            Tile.SOUTH, Tile.SOUTH, Tile.SOUTH,
            Tile.WEST, Tile.WEST, Tile.WEST,
            Tile.RED
        ])
        self.context.players[0].hand.fixed_groups = [
            TileGroup([Tile.NORTH] * 3, TileGroup.PONG)
        ]
        self.context.players[0].extra.update({
            'win_type': 'melded',
            'chucker': 1
        })

        self.context.players[1].hand.last_tile = Tile.RED
        self.context.discard(Tile.RED, 1)

        self.assertEqual(patterns.match_all(self.context, 0), {
            'big-four-winds': MatchResult(1, 1),
            'all-honors': MatchResult(1, 1)
        })

        # small-four-winds
        self.context.players[0].hand.free_tiles = [
            Tile.EAST, Tile.EAST, Tile.EAST,
            Tile.SOUTH, Tile.SOUTH, Tile.SOUTH,
            Tile.WEST, Tile.RED, Tile.RED, Tile.RED
        ]
        self.context.players[1].hand.last_tile = Tile.WEST
        self.context.discard(Tile.WEST, 1)

        self.assertEqual(patterns.match_all(self.context, 0), {
            'wind-seat': MatchResult(1, 1, extra=Tile.EAST),
            'wind-round': MatchResult(1, 1, extra=Tile.SOUTH),
            'dragons': MatchResult(1, 1, extra=[Tile.RED]),
            'small-four-winds': MatchResult(1, 1),
            'all-honors': MatchResult(1, 1)
        })

        # big-three-dragons
        self.context.players[0].hand.free_tiles = [
            Tile.EAST, Tile.EAST, Tile.EAST, Tile.WEST,
            Tile.RED, Tile.RED, Tile.RED,
            Tile.GREEN, Tile.GREEN, Tile.GREEN,
        ]
        self.context.players[0].hand.fixed_groups = [
            TileGroup([Tile.WHITE] * 4, TileGroup.KONG_CONCEALED),
            TileGroup([Tile.SOUTH] * 3, TileGroup.PONG)
        ]

        self.context.players[1].hand.last_tile = Tile.WEST
        self.context.discard(Tile.WEST, 1)

        self.assertEqual(patterns.match_all(self.context, 0), {
            'big-three-dragons': MatchResult(1, 1),
            'all-honors': MatchResult(1, 1),
            'wind-seat': MatchResult(1, 1, extra=Tile.EAST),
            'wind-round': MatchResult(1, 1, extra=Tile.SOUTH)
        })

        # small-three-dragons
        self.context.players[0].hand.free_tiles = [
            Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
            Tile.CIRCLE5, Tile.CIRCLE5, Tile.CIRCLE5,
            Tile.RED, Tile.RED, Tile.RED, Tile.GREEN
        ]
        self.context.players[0].hand.last_tile = Tile.GREEN
        self.context.players[0].extra.update({
            'win_type': 'self-picked',
            'chucker': None
        })

        self.assertEqual(patterns.match_all(self.context, 0), {
            'small-three-dragons': MatchResult((1, 2, 3), 1),
            'all-pongs': MatchResult((1, 2, 3), 1),
            'wind-round': MatchResult((1, 2, 3), 1, extra=Tile.SOUTH)
        })

        # mix-a-suit
        self.context.players[0].hand.free_tiles = [
            Tile.CIRCLE1, Tile.CIRCLE1, Tile.CIRCLE1,
            Tile.CIRCLE5, Tile.CIRCLE6,
            Tile.GREEN, Tile.GREEN, Tile.GREEN
        ]
        self.context.players[0].hand.fixed_groups = [
            TileGroup([Tile.WHITE] * 4, TileGroup.KONG_EXPOSED),
        ]
        self.context.players[0].hand.last_tile = Tile.CIRCLE7

        self.assertEqual(patterns.match_all(self.context, 0), {
            'mix-a-suit': MatchResult((1, 2, 3), 1),
            'dragons': MatchResult((1, 2, 3), 2, extra=[Tile.GREEN, Tile.WHITE])
        })


class TestMatchResult(unittest.TestCase):

    def test_non_zero(self):
        self.assertFalse(patterns.MatchResult())
        self.assertTrue(patterns.MatchResult(0, 1))
        self.assertTrue(patterns.MatchResult(1, 1))
        self.assertTrue(patterns.MatchResult(2, 1))
        self.assertTrue(patterns.MatchResult(3, 1))

    def test_iter(self):
        m = patterns.MatchResult()
        m.set(0, 9)
        m.set(1, 8)
        m.set(2, 7)
        m.set(3, 6)
        self.assertEqual(list(m), [9, 8, 7, 6])

    def test_equality(self):
        m1 = patterns.MatchResult()
        m2 = patterns.MatchResult()
        self.assertEqual(m1, m2)

        m1.set(0, 1)
        self.assertNotEqual(m1, m2)

        m2.set(0, 1)
        self.assertEqual(m1, m2)

        m1.extra = 'hello'
        m2.extra = 'world'
        self.assertNotEqual(m1, m2)

        m2.extra = 'hello'
        self.assertEqual(m1, m2)

        m1.set((1, 2, 3), 9)
        self.assertNotEqual(m1, m2)

        m2.set((1, 2, 3), 9)
        self.assertEqual(m1, m2)

    def test_repr(self):
        m = patterns.MatchResult((1, 2), 2, extra='hello')
        m.set(3, 10)
        self.assertEqual(repr(m), '([0, 2, 2, 10], hello)')

    def test_set_and_get(self):
        m = patterns.MatchResult()
        m.set((1, 3), 4)
        m.set(0, 6)
        m.set(2, 5)

        self.assertEqual(list(m), [6, 4, 5, 4])
        self.assertEqual(m.get(0), 6)
        self.assertEqual(m.get(1), 4)
        self.assertEqual(m.get(2), 5)
        self.assertEqual(m.get(3), 4)

    def test_clone(self):
        m1 = patterns.MatchResult((0, 1), 100, extra='hello')
        m2 = m1.clone()

        self.assertEqual(m1, m2)

        m2.set(0, 0)
        m2.extra = 'world'
        self.assertNotEqual(m1, m2)
        self.assertEqual(m1.get(0), 100)
        self.assertEqual(m2.get(0), 0)
        self.assertEqual(m1.extra, 'hello')
        self.assertEqual(m2.extra, 'world')


class TestPattern(unittest.TestCase):

    def test_match(self):
        pattern = patterns.Pattern()
        with self.assertRaises(NotImplementedError):
            pattern.match(None, None, None)

        with self.assertRaises(NotImplementedError):
            pattern.intersect(None, None, None)

    def test_mutual_exclusion(self):
        '''If pattern A excludes B, B should also excludes A.'''
        for name, pattern in patterns._PATTERNS.items():
            if pattern.excludes:
                for other_name in pattern.excludes:
                    other_pattern = patterns.get(other_name)
                    self.assertIn(name, other_pattern.excludes)


class TestDealer(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()
        self.context.dealer = 3

    def test_no_dealer_involved(self):
        # a non-dealer (player 1) wins from another non-dealer (player 2)
        self.context.winners = [1]
        self.context.players[1].extra.update({
            'win_type': 'melded',
            'chucker': 2
        })
        self.assertFalse(patterns.match('dealer', self.context, 1, Tile.CHAR1))

    def test_nondealer_self_picked(self):
        # a non-dealer (player 1) self-picks
        self.context.winners = [1]
        self.context.players[1].hand.last_tile = Tile.CHAR1
        self.context.players[1].extra['win_type'] = 'self-picked'

        result = patterns.match('dealer', self.context, 1)
        self.assertTrue(result)
        self.assertEqual(result.get(0), 0)
        self.assertEqual(result.get(1), 0)
        self.assertEqual(result.get(2), 0)
        self.assertEqual(result.get(3), 1)

    def test_dealer_self_picked(self):
        # dealer (player 3) self-picks
        self.context.winners = [3]
        self.context.players[3].hand.last_tile = Tile.CHAR1
        self.context.players[3].extra['win_type'] = 'self-picked'

        result = patterns.match('dealer', self.context, 3)
        self.assertTrue(result)
        self.assertEqual(result.get(0), 1)
        self.assertEqual(result.get(1), 1)
        self.assertEqual(result.get(2), 1)
        self.assertEqual(result.get(3), 0)

    def test_dealer_wins(self):
        # dealer (player 3) wins by melding player 2's discarded tile
        self.context.winners = [3]
        self.context.players[3].extra.update({
            'win_type': 'melded',
            'chucker': 2
        })

        result = patterns.match('dealer', self.context, 3, Tile.CHAR1)
        self.assertTrue(result)
        self.assertEqual(result.get(0), 0)
        self.assertEqual(result.get(1), 0)
        self.assertEqual(result.get(2), 1)
        self.assertEqual(result.get(3), 0)

    def test_dealer_chucks(self):
        # dealer (player 3) chucks to player 1
        self.context.winners = [1]
        self.context.players[1].extra.update({
            'win_type': 'melded',
            'chucker': 3
        })

        result = patterns.match('dealer', self.context, 1, Tile.CHAR1)
        self.assertTrue(result)
        self.assertEqual(result.get(0), 0)
        self.assertEqual(result.get(1), 0)
        self.assertEqual(result.get(2), 0)
        self.assertEqual(result.get(3), 1)


class TestDealerDefended(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()
        self.context.dealer = 3
        self.context.dealer_defended = 5

    def test_no_dealer_involved(self):
        # a non-dealer (player 1) wins from another non-dealer (player 2)
        self.context.winners = [1]
        self.context.players[1].extra.update({
            'win_type': 'melded',
            'chucker': 2
        })
        self.assertFalse(patterns.match('dealer-defended', self.context, 1, Tile.CHAR1))

    def test_nondealer_self_picked(self):
        # a non-dealer (player 1) self-picks
        self.context.winners = [1]
        self.context.players[1].hand.last_tile = Tile.CHAR1
        self.context.players[1].extra['win_type'] = 'self-picked'

        result = patterns.match('dealer-defended', self.context, 1)
        self.assertTrue(result)
        self.assertEqual(list(result), [0, 0, 0, 5])

    def test_dealer_self_picked(self):
        # dealer (player 3) self-picks
        self.context.winners = [3]
        self.context.players[3].hand.last_tile = Tile.CHAR1
        self.context.players[3].extra['win_type'] = 'self-picked'

        result = patterns.match('dealer-defended', self.context, 3)
        self.assertTrue(result)
        self.assertEqual(list(result), [5, 5, 5, 0])

    def test_dealer_wins(self):
        # dealer (player 3) wins by melding player 2's discarded tile
        self.context.winners = [3]
        self.context.players[3].extra.update({
            'win_type': 'melded',
            'chucker': 2
        })

        result = patterns.match('dealer-defended', self.context, 3, Tile.CHAR1)
        self.assertTrue(result)
        self.assertEqual(list(result), [0, 0, 5, 0])

    def test_dealer_chucks(self):
        # dealer (player 3) chucks to player 1
        self.context.winners = [1]
        self.context.players[1].extra.update({
            'win_type': 'melded',
            'chucker': 3
        })

        result = patterns.match('dealer-defended', self.context, 1, Tile.CHAR1)
        self.assertTrue(result)
        self.assertEqual(list(result), [0, 0, 0, 5])


class TestDeclaredReady(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_declared_ready(self):
        # not marked as declared_ready
        result = patterns.match('declared-ready', self.context, 2, Tile.CHAR1)
        self.assertFalse(result)

        # mark it as declared_ready and self-picked
        self.context.players[2].extra.update({
            'declared_ready': True,
            'win_type': 'self-picked'
        })
        result = patterns.match('declared-ready', self.context, 2, Tile.CHAR1)
        self.assertTrue(result)
        self.assertEqual(list(result), [1, 1, 0, 1])

        # wins by melding
        self.context.players[2].extra.update({
            'win_type': 'melded',
            'chucker': 3
        })
        result = patterns.match('declared-ready', self.context, 2, Tile.CHAR1)
        self.assertTrue(result)
        self.assertEqual(list(result), [0, 0, 0, 1])

        # should exclude flower-won
        self.context.players[2].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('declared-ready', self.context, 2, Tile.CHAR1))


class TestWindSeat(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_wind_seat(self):
        self.context.players[1].extra.update({
            'win_type': 'melded',
            'chucker': 0
        })
        self.context.players[3].extra.update({
            'win_type': 'melded',
            'chucker': 0
        })

        self.assertFalse(patterns.match('wind-seat', self.context, 1, Tile.CHAR1))
        self.assertFalse(patterns.match('wind-seat', self.context, 3, Tile.CHAR1))

        # two winds is not enough
        self.context.players[1].hand.add_free_tiles([
            Tile.SOUTH, Tile.SOUTH
        ])
        self.assertFalse(patterns.match('wind-seat', self.context, 1, Tile.CHAR1))

        # three winds is enough
        self.context.players[1].hand.add_free_tile(Tile.SOUTH)
        result = patterns.match('wind-seat', self.context, 1, Tile.CHAR1)
        self.assertEqual(list(result), [1, 0, 0, 0])
        self.assertEqual(result.extra, Tile.SOUTH)

        # player 3 should be at NORTH seat, giving it wrong winds shouldn't work
        self.context.players[3].hand.fixed_groups += [
            TileGroup([Tile.EAST] * 3, TileGroup.PONG),
            TileGroup([Tile.SOUTH] * 3, TileGroup.PONG),
            TileGroup([Tile.WEST] * 3, TileGroup.PONG),
        ]
        self.assertFalse(patterns.match('wind-seat', self.context, 3, Tile.CHAR1))

        # give player 3 NORTH tiles
        self.context.players[3].hand.fixed_groups.append(
            TileGroup([Tile.NORTH] * 3, TileGroup.PONG))
        result = patterns.match('wind-seat', self.context, 3, Tile.CHAR1)
        self.assertEqual(list(result), [1, 0, 0, 0])
        self.assertEqual(result.extra, Tile.NORTH)

        # make player 3 self-picked
        self.context.players[3].extra.update({
            'win_type': 'self-picked',
            'chucker': None
        })
        self.context.players[3].hand.last_tile = Tile.CHAR1
        result = patterns.match('wind-seat', self.context, 3)
        self.assertEqual(list(result), [1, 1, 1, 0])
        self.assertEqual(result.extra, Tile.NORTH)

        # should exclude flower-won
        self.context.players[3].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('wind-seat', self.context, 3))


class TestWindRound(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_wind_round(self):
        self.context.players[0].extra.update({
            'win_type': 'melded',
            'chucker': 1
        })
        self.context.players[2].extra.update({
            'win_type': 'melded',
            'chucker': 1
        })

        self.context.players[0].hand.add_free_tiles([
            Tile.EAST, Tile.EAST,
            Tile.SOUTH, Tile.SOUTH, Tile.SOUTH,
            Tile.NORTH, Tile.NORTH, Tile.NORTH
        ])
        self.context.players[2].hand.fixed_groups += [
            TileGroup([Tile.EAST] * 3, TileGroup.PONG),
            TileGroup([Tile.WEST] * 4, TileGroup.KONG_CONCEALED),
            TileGroup([Tile.NORTH] * 3, TileGroup.PONG),
        ]

        # round 0 is EAST round
        self.assertFalse(patterns.match('wind-round', self.context, 0, Tile.CHAR1))
        result = patterns.match('wind-round', self.context, 2, Tile.CHAR1)
        self.assertEqual(list(result), [0, 1, 0, 0])
        self.assertEqual(result.extra, Tile.EAST)

        # round 1 is SOUTH round
        self.context.round = 1
        self.assertFalse(patterns.match('wind-round', self.context, 2, Tile.CHAR1))
        result = patterns.match('wind-round', self.context, 0, Tile.CHAR1)
        self.assertEqual(list(result), [0, 1, 0, 0])
        self.assertEqual(result.extra, Tile.SOUTH)

        # round 11 is NORTH round
        self.context.round = 11
        result = patterns.match('wind-round', self.context, 0, Tile.CHAR1)
        self.assertEqual(list(result), [0, 1, 0, 0])
        self.assertEqual(result.extra, Tile.NORTH)
        result = patterns.match('wind-round', self.context, 2, Tile.CHAR1)
        self.assertEqual(list(result), [0, 1, 0, 0])
        self.assertEqual(result.extra, Tile.NORTH)

        # round 14 is WEST round, also test self-picked
        self.context.round = 14
        for i in (0, 2):
            self.context.players[i].extra.update({
                'win_type': 'self-picked',
                'chucker': None
            })
            self.context.players[i].hand.last_tile = Tile.CHAR1
        self.assertFalse(patterns.match('wind-round', self.context, 0))
        result = patterns.match('wind-round', self.context, 2)
        self.assertEqual(list(result), [1, 1, 0, 1])
        self.assertEqual(result.extra, Tile.WEST)

        # should exclude flower-won
        self.context.players[2].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('wind-round', self.context, 2))


class TestDragon(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_dragons(self):
        self.context.players[2].hand.add_free_tiles([
            Tile.GREEN, Tile.GREEN, Tile.GREEN,
            Tile.RED, Tile.RED
        ])
        self.context.players[2].hand.fixed_groups += [
            TileGroup([Tile.WHITE] * 3, TileGroup.PONG)
        ]

        result = patterns.match('dragons', self.context, 2, Tile.CHAR1)
        self.assertEqual(list(result), [2, 2, 0, 2])
        self.assertEqual(result.extra, [Tile.GREEN, Tile.WHITE])

        self.context.players[2].extra.update({
            'win_type': 'melded',
            'chucker': 0
        })

        result = patterns.match('dragons', self.context, 2, Tile.RED)
        self.assertEqual(list(result), [3, 0, 0, 0])
        self.assertEqual(result.extra, [Tile.RED, Tile.GREEN, Tile.WHITE])

        # should exclude flower-won
        self.context.players[2].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('dragons', self.context, 2, Tile.RED))


class FlowerSeat(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_flower_seat(self):
        # player 3 gets score only if he gets WINTER or CHRYSANTH
        # now he doesn't get any
        self.context.players[3].hand.flowers += [
            Tile.SPRING, Tile.SUMMER, Tile.AUTUMN,
            Tile.PLUM, Tile.ORCHID, Tile.BAMBOO
        ]

        self.assertFalse(patterns.match('flower-seat', self.context, 3, Tile.CHAR1))

        # player 3 gets his seat flowers
        self.context.players[3].hand.flowers += [Tile.WINTER, Tile.CHRYSANTH]

        result = patterns.match('flower-seat', self.context, 3, Tile.CHAR1)
        self.assertEqual(list(result), [2, 2, 2, 0])
        self.assertEqual(result.extra, [Tile.CHRYSANTH, Tile.WINTER])

        self.context.players[3].extra.update({
            'win_type': 'melded',
            'chucker': 1
        })
        result = patterns.match('flower-seat', self.context, 3, Tile.CHAR1)
        self.assertEqual(list(result), [0, 2, 0, 0])
        self.assertEqual(result.extra, [Tile.CHRYSANTH, Tile.WINTER])

        # should exclude flower-won
        self.context.players[3].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('flower-seat', self.context, 3, Tile.CHAR1))


class TestFourFlowers(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_four_flowers(self):
        # player 2 has four ungroupable flowers
        self.context.players[2].hand.flowers += [
            Tile.SPRING, Tile.ORCHID, Tile.CHRYSANTH, Tile.PLUM
        ]

        self.assertFalse(patterns.match('four-flowers', self.context, 2, Tile.CHAR1))

        # four special flowers collected
        self.context.players[2].hand.flowers.append(Tile.BAMBOO)
        result = patterns.match('four-flowers', self.context, 2, Tile.CHAR1)
        self.assertEqual(list(result), [1, 1, 0, 1])
        self.assertEqual(result.extra, ['flowers'])

        self.context.players[2].extra.update({
            'win_type': 'melded',
            'chucker': 1
        })

        # four seasons collected
        self.context.players[2].hand.flowers += [
            Tile.SUMMER, Tile.AUTUMN, Tile.WINTER
        ]
        result = patterns.match('four-flowers', self.context, 2, Tile.CHAR1)
        self.assertEqual(list(result), [0, 2, 0, 0])
        self.assertEqual(result.extra, ['flowers', 'seasons'])

        # should exclude flower-won
        self.context.players[2].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('four-flowers', self.context, 2, Tile.CHAR1))


class TestConcealedTriplets(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_concealed_triplets(self):
        # waiting for CHAR2 and NORTH
        self.context.players[0].hand.add_free_tiles([
            Tile.CHAR1, Tile.CHAR2, Tile.CHAR2, Tile.CHAR2,
            Tile.CHAR3, Tile.CIRCLE3, Tile.CIRCLE3, Tile.CIRCLE3,
            Tile.BAMBOO6, Tile.BAMBOO6, Tile.BAMBOO6,
            Tile.NORTH, Tile.NORTH,
        ])

        # exposed tiles shouldn't be counted into concealed triplets
        self.context.players[0].hand.fixed_groups += [
            TileGroup([Tile.GREEN] * 3, TileGroup.PONG)
        ]

        self.assertFalse(patterns.match('three-concealed-triplets', self.context, 0, Tile.CHAR1))

        # NORTH taken from others can't be considered concealed
        self.assertFalse(patterns.match('three-concealed-triplets', self.context, 0, Tile.NORTH))

        # NORTH picked by self is considered concealed
        self.context.players[0].hand.last_tile = Tile.NORTH
        result = patterns.match('three-concealed-triplets', self.context, 0)
        self.assertEqual(list(result), [0, 1, 1, 1])

        # undo
        self.context.players[0].hand.last_tile = None

        # give him three REDs, now he has three concealed triplets
        self.context.players[0].hand.add_free_tiles([Tile.RED] * 3)

        print self.context.players[0].hand

        result = patterns.match('three-concealed-triplets', self.context, 0, Tile.NORTH)
        self.assertEqual(list(result), [0, 1, 1, 1])

        # NORTH doesn't count as concealed
        self.assertFalse(patterns.match('four-concealed-triplets', self.context, 0, Tile.NORTH))

        # give him a SOUTH concealed kongs, now he has four concealed triplets
        self.context.players[0].hand.fixed_groups += [
            TileGroup([Tile.SOUTH] * 4, TileGroup.KONG_CONCEALED)
        ]
        result = patterns.match('three-concealed-triplets', self.context, 0, Tile.NORTH)
        self.assertEqual(list(result), [0, 1, 1, 1])
        result = patterns.match('four-concealed-triplets', self.context, 0, Tile.NORTH)
        self.assertEqual(list(result), [0, 1, 1, 1])

        self.assertFalse(patterns.match('five-concealed-triplets', self.context, 0, Tile.NORTH))

        self.context.players[0].extra.update({
            'win_type': 'melded',
            'chucker': 2
        })

        # give him three WESTs, now he has five concealed triplets
        self.context.players[0].hand.add_free_tiles([Tile.WEST] * 3)
        result = patterns.match('three-concealed-triplets', self.context, 0, Tile.NORTH)
        self.assertEqual(list(result), [0, 0, 1, 0])
        result = patterns.match('four-concealed-triplets', self.context, 0, Tile.NORTH)
        self.assertEqual(list(result), [0, 0, 1, 0])
        result = patterns.match('five-concealed-triplets', self.context, 0, Tile.NORTH)
        self.assertEqual(list(result), [0, 0, 1, 0])

        # should exclude flower-won
        self.context.players[0].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('three-concealed-triplets', self.context, 0, Tile.NORTH))
        self.assertFalse(patterns.match('four-concealed-triplets', self.context, 0, Tile.NORTH))
        self.assertFalse(patterns.match('five-concealed-triplets', self.context, 0, Tile.NORTH))

    def test_counter_examples(self):
        # this hand can win with (777, 888, 789, 99),
        # but shouldn't have three concealed triplets
        self.context.players[0].hand.add_free_tiles([
            Tile.CHAR7, Tile.CHAR7, Tile.CHAR7,
            Tile.CHAR8, Tile.CHAR8, Tile.CHAR8,
            Tile.CHAR7, Tile.CHAR8, Tile.CHAR9,
            Tile.CHAR9
        ])
        self.context.players[0].hand.last_tile = Tile.CHAR9
        self.assertFalse(patterns.match('three-concealed-triplets', self.context, 0))

        self.context.players[0].hand.add_free_tiles([
            Tile.CHAR7, Tile.CHAR7, Tile.CHAR7,
            Tile.CHAR8, Tile.CHAR8, Tile.CHAR8,
            Tile.CHAR7, Tile.CHAR8, Tile.CHAR9,
            Tile.CHAR9,
            Tile.EAST, Tile.EAST, Tile.EAST
        ])
        self.context.players[0].hand.last_tile = Tile.CHAR9
        self.assertFalse(patterns.match('four-concealed-triplets', self.context, 0))

        self.context.players[0].hand.add_free_tiles([
            Tile.CHAR7, Tile.CHAR7, Tile.CHAR7,
            Tile.CHAR8, Tile.CHAR8, Tile.CHAR8,
            Tile.CHAR7, Tile.CHAR8, Tile.CHAR9,
            Tile.CHAR9,
            Tile.EAST, Tile.EAST, Tile.EAST,
            Tile.RED, Tile.RED, Tile.RED
        ])
        self.context.players[0].hand.last_tile = Tile.CHAR9
        self.assertFalse(patterns.match('five-concealed-triplets', self.context, 0))


class TestAllPongs(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_all_pongs(self):
        # player 0 has a sequence
        self.context.players[0].hand.add_free_tiles([
            Tile.CHAR7, Tile.CIRCLE3, Tile.CIRCLE4, Tile.CIRCLE5
        ])

        # player 1 has a chow
        self.context.players[1].hand.add_free_tiles([
            Tile.CHAR7, Tile.RED, Tile.RED, Tile.RED
        ])
        self.context.players[1].hand.fixed_groups += [
            TileGroup([Tile.BAMBOO5, Tile.BAMBOO6, Tile.BAMBOO7], TileGroup.CHOW),
        ]

        # player 2 has only pairs and triplets
        self.context.players[2].hand.add_free_tiles([
            Tile.CHAR7, Tile.CHAR7,
            Tile.CIRCLE9, Tile.CIRCLE9,
            Tile.EAST, Tile.EAST, Tile.EAST
        ])
        self.context.players[2].hand.fixed_groups += [
            TileGroup([Tile.CHAR6] * 4, TileGroup.KONG_EXPOSED),
            TileGroup([Tile.GREEN] * 3, TileGroup.PONG),
            TileGroup([Tile.CHAR2] * 4, TileGroup.KONG_CONCEALED)
        ]

        self.assertFalse(patterns.match('all-pongs', self.context, 0, Tile.CHAR7))
        self.assertFalse(patterns.match('all-pongs', self.context, 1, Tile.CHAR7))

        result = patterns.match('all-pongs', self.context, 2, Tile.CHAR7)
        self.assertEqual(list(result), [1, 1, 0, 1])

        self.context.players[2].extra.update({
            'win_type': 'melded',
            'chucker': 3
        })

        result = patterns.match('all-pongs', self.context, 2, Tile.CHAR7)
        self.assertEqual(list(result), [0, 0, 0, 1])

        # should exclude flower-won
        self.context.players[2].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('all-pongs', self.context, 2, Tile.CHAR7))


class TestPurelyConcealedSelfPicked(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_purely_concealed_self_picked(self):
        self.context.players[1].hand.add_free_tile(Tile.CHAR2)
        self.context.players[1].extra.update({
            'win_type': 'melded',
            'chucker': 3
        })

        # purely-concealed but not self-picked
        self.assertFalse(patterns.match('self-picked', self.context, 1, Tile.CHAR2))
        self.assertFalse(patterns.match('purely-concealed-self-picked', self.context, 1, Tile.CHAR2))

        result = patterns.match('purely-concealed', self.context, 1, Tile.CHAR2)
        self.assertEqual(list(result), [0, 0, 0, 1])

        # make player 1 self-picked
        self.context.players[1].hand.last_tile = Tile.CHAR2
        self.context.players[1].extra.update({
            'win_type': 'self-picked',
            'chucker': None
        })

        # add concealed kongs, purely-concealed should still counts
        self.context.players[1].hand.fixed_groups += [
            TileGroup([Tile.CHAR3] * 4, TileGroup.KONG_CONCEALED),
            TileGroup([Tile.CHAR6] * 4, TileGroup.KONG_CONCEALED)
        ]

        # should exclude flower-won
        self.context.players[1].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('self-picked', self.context, 1))
        self.assertFalse(patterns.match('purely-concealed', self.context, 1))
        self.assertFalse(patterns.match('purely-concealed-self-picked', self.context, 1))

        self.context.players[1].extra['win_type'] = 'self-picked'

        result = patterns.match('self-picked', self.context, 1)
        self.assertEqual(list(result), [1, 0, 1, 1])

        result = patterns.match('purely-concealed', self.context, 1)
        self.assertEqual(list(result), [1, 0, 1, 1])

        result = patterns.match('purely-concealed-self-picked', self.context, 1)
        self.assertEqual(list(result), [1, 0, 1, 1])

        # make player 1 not purely-concealed
        self.context.players[1].hand.fixed_groups += [
            TileGroup([Tile.CHAR3] * 4, TileGroup.KONG_EXPOSED)
        ]

        self.assertFalse(patterns.match('purely-concealed', self.context, 1))
        self.assertFalse(patterns.match('purely-concealed-self-picked', self.context, 1))

        result = patterns.match('self-picked', self.context, 1)
        self.assertEqual(list(result), [1, 0, 1, 1])

        # if there's pong, it's not purely-concealed
        self.context.players[1].hand.fixed_groups = [
            TileGroup([Tile.CHAR3] * 3, TileGroup.PONG)
        ]
        self.assertFalse(patterns.match('purely-concealed', self.context, 1))
        self.assertFalse(patterns.match('purely-concealed-self-picked', self.context, 1))

        # if there's chow, it's not purely-concealed
        self.context.players[1].hand.fixed_groups = [
            TileGroup([Tile.CHAR3, Tile.CHAR4, Tile.CHAR5], TileGroup.CHOW)
        ]
        self.assertFalse(patterns.match('purely-concealed', self.context, 1))
        self.assertFalse(patterns.match('purely-concealed-self-picked', self.context, 1))


class TestSevenFlowers(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_seven_flowers(self):
        self.context.cur_player_idx = 2
        self.context.players[0].hand.flowers = Tile.FLOWERS[0:7]

        self.assertFalse(patterns.match('seven-flowers', self.context, 0, Tile.CHAR1))

        result = patterns.match('seven-flowers', self.context, 0, Tile.WINTER)
        self.assertEqual(list(result), [0, 0, 1, 0])

        self.context.players[0].hand.flowers.append(Tile.WINTER)
        self.context.extra['flower_chucker'] = 3

        result = patterns.match('seven-flowers', self.context, 0, Tile.CHAR1)
        self.assertEqual(list(result), [0, 0, 0, 1])


class TestEightFlowers(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_eight_flowers(self):
        self.context.players[0].hand.flowers = Tile.FLOWERS[0:7]

        self.assertFalse(patterns.match('eight-flowers', self.context, 0, Tile.CHAR1))

        self.context.players[0].hand.last_tile = Tile.WINTER
        result = patterns.match('eight-flowers', self.context, 0, Tile.WINTER)
        self.assertEqual(list(result), [0, 1, 1, 1])

        self.context.players[0].hand.move_flowers()
        result = patterns.match('eight-flowers', self.context, 0, Tile.CHAR1)
        self.assertEqual(list(result), [0, 1, 1, 1])

        # if flower_chucker exists, then it's seven-flowers instead of eight-flowers
        self.context.extra['flower_chucker'] = 3
        self.assertFalse(patterns.match('eight-flowers', self.context, 0, Tile.CHAR1))


class TestFlowerWinAfterDealing(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_flower_win_after_dealing(self):
        self.context.players[0].hand.flowers = Tile.FLOWERS

        result = patterns.match('flower-win-after-dealing', self.context, 0, Tile.CHAR1)
        self.assertEqual(list(result), [0, 1, 1, 1])

        self.context.extra['flower_chucker'] = 3
        result = patterns.match('flower-win-after-dealing', self.context, 0, Tile.CHAR1)
        self.assertEqual(list(result), [0, 0, 0, 1])

        self.context.players[0].hand.add_free_tile(Tile.CHAR1)
        self.context.discard(Tile.CHAR1, 0)
        self.assertFalse(patterns.match('flower-win-after-dealing', self.context, 0, Tile.CHAR1))


class TestHeavenWin(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()
        self.context.dealer = 1

    def test_heaven_win(self):
        # player 2 is not dealer, so it's not heaven-win
        self.context.players[2].hand.last_tile = Tile.CHAR1
        self.assertFalse(patterns.match('heaven-win', self.context, 2))

        # player 1 wins with flowers -> doesn't count as heaven-win
        self.context.players[1].extra['win_type'] = 'flower-won'
        self.context.players[1].hand.last_tile = Tile.CHAR1
        self.assertFalse(patterns.match('heaven-win', self.context, 1))

        # player 1 self-picks on his first drawing -> heaven-win
        self.context.players[1].extra['win_type'] = 'self-picked'
        result = patterns.match('heaven-win', self.context, 1)
        self.assertEqual(list(result), [1, 0, 1, 1])

        # someone has discarded a tile, no more heaven-win
        self.context.discard(Tile.CHAR1, 1)
        self.context.players[1].hand.last_tile = Tile.CHAR1
        self.assertFalse(patterns.match('heaven-win', self.context, 1))


class TestEarthWin(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()
        self.context.dealer = 1

    def test_earth_win(self):
        # player 1 is dealer, so it's heaven-win instead of earth-win
        self.context.players[1].hand.last_tile = Tile.CHAR1
        self.assertFalse(patterns.match('earth-win', self.context, 1))
        result = patterns.match('heaven-win', self.context, 1)
        self.assertEqual(list(result), [1, 0, 1, 1])

        # player 2 wins with flowers -> doesn't count as earth-win
        self.context.players[2].extra['win_type'] = 'flower-won'
        self.context.players[2].hand.last_tile = Tile.CHAR1
        self.assertFalse(patterns.match('earth-win', self.context, 2))

        # player 2 self-picks on his first drawing -> earth-win
        self.context.players[2].extra['win_type'] = 'self-picked'
        result = patterns.match('earth-win', self.context, 2)
        self.assertEqual(list(result), [1, 1, 0, 1])

        # the player has discarded a tile, no more earth-win
        self.context.discard(Tile.CHAR1, 2)
        self.context.players[2].hand.last_tile = Tile.CHAR1
        self.assertFalse(patterns.match('earth-win', self.context, 1))


class TestHumanWin(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_human_win(self):
        self.context.players[3].extra.update({
            'win_type': 'melded',
            'chucker': 0
        })

        # no tiles in discarded pool yet
        self.assertFalse(patterns.match('human-win', self.context, 3, Tile.CHAR1))

        self.context.players[0].hand.add_free_tiles([
            Tile.CHAR1, Tile.CHAR2, Tile.CHAR3
        ])
        self.context.discard(Tile.CHAR1, 0)

        result = patterns.match('human-win', self.context, 3, Tile.CHAR1)
        self.assertEqual(list(result), [1, 0, 0, 0])

        # flower win shouldn't count
        self.context.players[3].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('human-win', self.context, 3, Tile.CHAR1))


class TestHeavenReady(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_heaven_ready(self):
        self.assertFalse(patterns.match('heaven-ready', self.context, 3, Tile.CHAR1))

        self.context.players[3].extra['immediate_ready'] = True
        self.assertFalse(patterns.match('heaven-ready', self.context, 3, Tile.CHAR1))

        self.context.dealer = 3
        result = patterns.match('heaven-ready', self.context, 3, Tile.CHAR1)
        self.assertEqual(list(result), [1, 1, 1, 0])

        self.context.players[3].extra.update({
            'win_type': 'melded',
            'chucker': 1
        })
        result = patterns.match('heaven-ready', self.context, 3, Tile.CHAR1)
        self.assertEqual(list(result), [0, 1, 0, 0])

        # flower win shouldn't count
        self.context.players[3].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('heaven-ready', self.context, 3, Tile.CHAR1))


class TestEarthReady(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_earth_ready(self):
        self.assertFalse(patterns.match('earth-ready', self.context, 0, Tile.CHAR1))

        self.context.players[0].extra['immediate_ready'] = True
        self.assertFalse(patterns.match('earth-ready', self.context, 0, Tile.CHAR1))

        self.context.dealer = 3
        result = patterns.match('earth-ready', self.context, 0, Tile.CHAR1)
        self.assertEqual(list(result), [0, 1, 1, 1])

        self.context.players[0].extra.update({
            'win_type': 'melded',
            'chucker': 1
        })
        result = patterns.match('earth-ready', self.context, 0, Tile.CHAR1)
        self.assertEqual(list(result), [0, 1, 0, 0])

        # flower win shouldn't count
        self.context.players[0].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('earth-ready', self.context, 0, Tile.CHAR1))


class TestFourWinds(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_four_winds(self):
        self.context.players[2].hand.add_free_tiles([
            Tile.WEST, Tile.WEST,
            Tile.NORTH, Tile.NORTH
        ])
        self.context.players[2].hand.fixed_groups += [
            TileGroup([Tile.EAST] * 3, TileGroup.PONG),
            TileGroup([Tile.SOUTH] * 4, TileGroup.KONG_CONCEALED)
        ]

        self.assertFalse(patterns.match('small-four-winds', self.context, 2, Tile.CHAR1))
        self.assertFalse(patterns.match('big-four-winds', self.context, 2, Tile.CHAR1))

        result = patterns.match('small-four-winds', self.context, 2, Tile.WEST)
        self.assertEqual(list(result), [1, 1, 0, 1])

        self.assertFalse(patterns.match('big-four-winds', self.context, 2, Tile.WEST))

        self.context.players[2].hand.add_free_tile(Tile.NORTH)
        self.context.players[2].extra.update({
            'win_type': 'melded',
            'chucker': 3
        })

        result = patterns.match('small-four-winds', self.context, 2, Tile.WEST)
        self.assertEqual(list(result), [0, 0, 0, 1])

        result = patterns.match('big-four-winds', self.context, 2, Tile.WEST)
        self.assertEqual(list(result), [0, 0, 0, 1])

        # flower win shouldn't count
        self.context.players[2].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('small-four-winds', self.context, 2, Tile.WEST))
        self.assertFalse(patterns.match('big-four-winds', self.context, 2, Tile.WEST))


class TestThreeDragons(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_three_dragons(self):
        self.context.players[1].hand.add_free_tiles([
            Tile.RED, Tile.RED,
            Tile.GREEN, Tile.GREEN
        ])
        self.context.players[1].hand.fixed_groups += [
            TileGroup([Tile.WHITE] * 3, TileGroup.PONG)
        ]

        self.assertFalse(patterns.match('small-three-dragons', self.context, 1, Tile.CHAR1))
        self.assertFalse(patterns.match('big-three-dragons', self.context, 1, Tile.CHAR1))

        result = patterns.match('small-three-dragons', self.context, 1, Tile.GREEN)
        self.assertEqual(list(result), [1, 0, 1, 1])

        self.assertFalse(patterns.match('big-three-dragons', self.context, 1, Tile.GREEN))

        self.context.players[1].hand.add_free_tile(Tile.RED)
        self.context.players[1].extra.update({
            'win_type': 'melded',
            'chucker': 0
        })

        result = patterns.match('small-three-dragons', self.context, 1, Tile.GREEN)
        self.assertEqual(list(result), [1, 0, 0, 0])

        result = patterns.match('big-three-dragons', self.context, 1, Tile.GREEN)
        self.assertEqual(list(result), [1, 0, 0, 0])

        # flower win shouldn't count
        self.context.players[1].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('small-three-dragons', self.context, 1, Tile.GREEN))
        self.assertFalse(patterns.match('big-three-dragons', self.context, 1, Tile.GREEN))


class TestAllHonors(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_all_honors(self):
        self.context.players[3].hand.add_free_tiles([
            Tile.RED, Tile.GREEN, Tile.EAST, Tile.SOUTH
        ])
        self.context.players[3].hand.fixed_groups += [
            TileGroup([Tile.WEST] * 3, TileGroup.PONG),
            TileGroup([Tile.NORTH] * 4, TileGroup.KONG_CONCEALED)
        ]

        result = patterns.match('all-honors', self.context, 3, Tile.RED)
        self.assertEqual(list(result), [1, 1, 1, 0])

        self.assertFalse(patterns.match('all-honors', self.context, 3, Tile.CHAR1))

        self.context.players[3].hand.fixed_groups += [
            TileGroup([Tile.CHAR2, Tile.CHAR3, Tile.CHAR4], TileGroup.CHOW)
        ]

        self.assertFalse(patterns.match('all-honors', self.context, 3, Tile.RED))

        self.context.players[3].hand.fixed_groups.pop()
        self.context.players[3].extra.update({
            'win_type': 'melded',
            'chucker': 0
        })
        result = patterns.match('all-honors', self.context, 3, Tile.RED)
        self.assertEqual(list(result), [1, 0, 0, 0])

        # flower win shouldn't count
        self.context.players[3].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('all-honors', self.context, 3, Tile.RED))

        # add a non-honor tile, then it's not all-honors
        self.context.players[3].extra['win_type'] = 'melded'
        self.context.players[3].hand.add_free_tile(Tile.CHAR1)
        self.assertFalse(patterns.match('all-honors', self.context, 3, Tile.RED))


class TestSameSuit(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_same_suit_chars(self):
        self.context.players[0].hand.add_free_tiles([
            Tile.CHAR1, Tile.CHAR2, Tile.CHAR3,
            Tile.CHAR5, Tile.CHAR5, Tile.CHAR5,
            Tile.CHAR7, Tile.CHAR8, Tile.CHAR9
        ])
        self.context.players[0].hand.fixed_groups += [
            TileGroup([Tile.CHAR2, Tile.CHAR3, Tile.CHAR4], TileGroup.CHOW),
            TileGroup([Tile.CHAR6] * 3, TileGroup.PONG)
        ]

        result = patterns.match('same-suit', self.context, 0, Tile.CHAR1)
        self.assertEqual(list(result), [0, 1, 1, 1])

        self.context.players[0].hand.last_tile = Tile.BAMBOO1
        self.assertFalse(patterns.match('same-suit', self.context, 0))

        self.context.players[0].hand.last_tile = None
        self.context.players[0].extra.update({
            'win_type': 'melded',
            'chucker': 1
        })

        result = patterns.match('same-suit', self.context, 0, Tile.CHAR1)
        self.assertEqual(list(result), [0, 1, 0, 0])

        self.context.players[0].hand.add_free_tile(Tile.CIRCLE1)
        self.assertFalse(patterns.match('same-suit', self.context, 0, Tile.CHAR1))

    def test_same_suit_bamboos(self):
        self.context.players[0].hand.add_free_tiles([
            Tile.BAMBOO1, Tile.BAMBOO2, Tile.BAMBOO3,
            Tile.BAMBOO7, Tile.BAMBOO7
        ])
        self.context.players[0].hand.fixed_groups += [
            TileGroup([Tile.BAMBOO3, Tile.BAMBOO4, Tile.BAMBOO5], TileGroup.CHOW),
            TileGroup([Tile.BAMBOO5] * 3, TileGroup.PONG)
        ]

        # flowers shouldn't affect same-suit
        self.context.players[0].hand.flowers += [Tile.SPRING, Tile.SUMMER]

        # flower win shouldn't count
        self.context.players[0].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('same-suit', self.context, 0, Tile.BAMBOO1))

        self.context.players[0].extra['win_type'] = 'melded'
        result = patterns.match('same-suit', self.context, 0, Tile.BAMBOO1)
        self.assertEqual(list(result), [0, 1, 1, 1])

        self.context.players[0].hand.last_tile = Tile.CHAR1
        self.assertFalse(patterns.match('same-suit', self.context, 0))

    def test_same_suit_honors(self):
        # same-suit mustn't contain honors
        self.context.players[0].hand.add_free_tiles([
            Tile.EAST, Tile.EAST, Tile.WEST, Tile.WEST
        ])
        self.assertFalse(patterns.match('same-suit', self.context, 0, Tile.WEST))


class TestMixASuit(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_mix_a_suit_chars(self):
        self.context.players[1].hand.add_free_tiles([
            Tile.CHAR3, Tile.CHAR3, Tile.CHAR6, Tile.CHAR7, Tile.CHAR8,
            Tile.EAST, Tile.EAST
        ])
        self.context.players[1].hand.fixed_groups += [
            TileGroup([Tile.NORTH] * 3, TileGroup.PONG),
            TileGroup([Tile.CHAR4, Tile.CHAR5, Tile.CHAR6], TileGroup.CHOW)
        ]

        self.assertFalse(patterns.match('mix-a-suit', self.context, 1, Tile.BAMBOO1))

        result = patterns.match('mix-a-suit', self.context, 1, Tile.EAST)
        self.assertEqual(list(result), [1, 0, 1, 1])

        self.context.players[1].hand.add_free_tile(Tile.CIRCLE1)
        self.context.players[1].extra.update({
            'win_type': 'melded',
            'chucker': 2
        })

        self.assertFalse(patterns.match('mix-a-suit', self.context, 1, Tile.CHAR1))

        self.context.players[1].hand.free_tiles.remove(Tile.CIRCLE1)
        result = patterns.match('mix-a-suit', self.context, 1, Tile.EAST)
        self.assertEqual(list(result), [0, 0, 1, 0])

    def test_mix_a_suit_circles(self):
        self.context.players[1].hand.add_free_tiles([
            Tile.CIRCLE2, Tile.CIRCLE3, Tile.CIRCLE6, Tile.CIRCLE6, Tile.CIRCLE6
        ])
        self.context.players[1].hand.fixed_groups += [
            TileGroup([Tile.CIRCLE7, Tile.CIRCLE8, Tile.CIRCLE9], TileGroup.CHOW)
        ]

        # flowers shouldn't affect mix-a-suit
        self.context.players[1].hand.flowers += [Tile.SUMMER, Tile.PLUM]

        self.assertFalse(patterns.match('mix-a-suit', self.context, 1, Tile.CIRCLE4))

        self.context.players[1].hand.fixed_groups += [
            TileGroup([Tile.WHITE] * 3, TileGroup.PONG)
        ]

        result = patterns.match('mix-a-suit', self.context, 1, Tile.CIRCLE4)
        self.assertEqual(list(result), [1, 0, 1, 1])

        # flower win shouldn't count
        self.context.players[1].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('mix-a-suit', self.context, 1, Tile.CIRCLE4))

    def test_mix_a_suit_honors(self):
        # all honors shouldn't count as mix-a-suit
        self.context.players[1].hand.add_free_tiles([
            Tile.EAST, Tile.EAST, Tile.NORTH, Tile.NORTH
        ])
        self.assertFalse(patterns.match('mix-a-suit', self.context, 1, Tile.EAST))

        self.context.players[1].hand.fixed_groups += [
            TileGroup([Tile.BAMBOO1, Tile.BAMBOO2, Tile.BAMBOO3], TileGroup.CHOW)
        ]
        result = patterns.match('mix-a-suit', self.context, 1, Tile.EAST)
        self.assertEqual(list(result), [1, 0, 1, 1])


class TestAllSequences(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()
        self.context.players[3].hand.add_free_tiles([
            Tile.CHAR5, Tile.CHAR6, Tile.CHAR7,
            Tile.CIRCLE2, Tile.CIRCLE3, Tile.CIRCLE4,
            Tile.BAMBOO5, Tile.BAMBOO6,
            Tile.BAMBOO9, Tile.BAMBOO9
        ])
        self.context.players[3].hand.fixed_groups += [
            TileGroup([Tile.CHAR7, Tile.CHAR8, Tile.CHAR9], TileGroup.CHOW),
            TileGroup([Tile.CIRCLE5, Tile.CIRCLE6, Tile.CIRCLE7], TileGroup.CHOW)
        ]

        self.context.players[3].extra.update({
            'win_type': 'melded',
            'chucker': 1
        })

    def test_all_sequences(self):
        # flower win shouldn't count
        self.context.players[3].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('all-sequences', self.context, 3, Tile.BAMBOO7))

        self.context.players[3].extra['win_type'] = 'melded'
        result = patterns.match('all-sequences', self.context, 3, Tile.BAMBOO7)
        self.assertEqual(list(result), [0, 1, 0, 0])

        # add a pong, then it's not all-sequences
        self.context.players[3].hand.fixed_groups += [
            TileGroup([Tile.CHAR1] * 3, TileGroup.PONG)
        ]
        self.assertFalse(patterns.match('all-sequences', self.context, 3, Tile.BAMBOO7))

        self.context.players[3].hand.fixed_groups.pop()
        self.context.players[3].hand.add_free_tiles([
            Tile.CHAR1, Tile.CHAR1, Tile.CHAR1
        ])
        self.assertFalse(patterns.match('all-sequences', self.context, 3, Tile.BAMBOO7))

    def test_all_sequences_self_picked(self):
        # all-sequences can't be self-picked
        self.context.players[3].extra.update({
            'win_type': 'self-picked',
            'chucker': None
        })

        self.assertFalse(patterns.match('all-sequences', self.context, 3, Tile.BAMBOO7))

        self.context.players[3].hand.last_tile = Tile.BAMBOO7
        self.assertFalse(patterns.match('all-sequences', self.context, 3))

    def test_all_sequences_flowers(self):
        # all-sequences mustn't contain flowers
        self.context.players[3].hand.add_flower(Tile.SPRING)
        self.assertFalse(patterns.match('all-sequences', self.context, 3, Tile.BAMBOO7))

    def test_all_sequences_honors(self):
        # all-sequences mustn't contain honors
        self.context.players[3].hand.fixed_groups += [
            TileGroup([Tile.RED] * 3, TileGroup.PONG)
        ]
        self.assertFalse(patterns.match('all-sequences', self.context, 3, Tile.BAMBOO7))

        self.context.players[3].hand.fixed_groups.pop()
        self.context.players[3].hand.add_free_tiles([
            Tile.WEST, Tile.WEST, Tile.WEST
        ])
        self.assertFalse(patterns.match('all-sequences', self.context, 3, Tile.BAMBOO7))

    def test_all_sequences_waiting_tiles(self):
        # all-sequences must have more than one waiting tile
        # this hand has only one waiting tile CIRCLE3, so it doesn't match all-sequences
        self.context.players[3].hand.free_tiles = [
            Tile.CHAR5, Tile.CHAR6, Tile.CHAR7,
            Tile.CIRCLE1, Tile.CIRCLE2,
            Tile.BAMBOO9, Tile.BAMBOO9
        ]
        self.assertFalse(patterns.match('all-sequences', self.context, 3, Tile.CIRCLE3))

    def test_all_sequences_no_pair(self):
        # doesn't have any pair, then is not all-sequences
        self.context.players[3].hand.free_tiles = [
            Tile.CHAR1, Tile.CHAR2, Tile.CHAR3,
            Tile.CIRCLE4, Tile.CIRCLE5, Tile.CIRCLE6,
            Tile.BAMBOO2, Tile.BAMBOO3
        ]
        self.assertFalse(patterns.match('all-sequences', self.context, 3, Tile.BAMBOO4))

    def test_all_sequences_one_pair(self):
        self.context.players[3].hand.free_tiles = [Tile.BAMBOO7]
        self.assertFalse(patterns.match('all-sequences', self.context, 3, Tile.BAMBOO7))

    def test_all_sequences_not_winning_hand(self):
        self.context.players[3].hand.free_tiles = [
            Tile.BAMBOO7, Tile.BAMBOO8, Tile.BAMBOO9
        ]
        self.assertFalse(patterns.match('all-sequences', self.context, 3, Tile.BAMBOO7))


class TestWaitingForOne(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_waiting_for_eye(self):
        # wait for CHAR5 eye
        self.context.players[0].hand.free_tiles = [
            Tile.CHAR1, Tile.CHAR2, Tile.CHAR3, Tile.CHAR5
        ]
        result = patterns.match('waiting-for-one', self.context, 0, Tile.CHAR5)
        self.assertEqual(list(result), [0, 1, 1, 1])
        self.assertEqual(result.extra, 'eye')

        # wait for RED eye
        self.context.players[0].hand.free_tiles = [
            Tile.CHAR1, Tile.CHAR2, Tile.CHAR3, Tile.RED
        ]
        result = patterns.match('waiting-for-one', self.context, 0, Tile.RED)
        self.assertEqual(list(result), [0, 1, 1, 1])
        self.assertEqual(result.extra, 'eye')

        # wait for BAMBOO6
        self.context.players[0].extra.update({
            'win_type': 'melded',
            'chucker': 2
        })
        self.context.players[0].hand.free_tiles = [
            Tile.CHAR3, Tile.CHAR4, Tile.CHAR5, Tile.CHAR5, Tile.CHAR6, Tile.CHAR7,
            Tile.BAMBOO6, Tile.RED, Tile.RED, Tile.RED
        ]

        # flowers shouldn't affect waiting-for-one
        self.context.players[0].hand.flowers = [Tile.SUMMER, Tile.ORCHID]

        result = patterns.match('waiting-for-one', self.context, 0, Tile.BAMBOO6)
        self.assertEqual(list(result), [0, 0, 1, 0])
        self.assertEqual(result.extra, 'eye')

        # wait for CIRCLE2 eye
        self.context.players[0].hand.free_tiles = [Tile.CIRCLE2]
        result = patterns.match('waiting-for-one', self.context, 0, Tile.CIRCLE2)
        self.assertEqual(list(result), [0, 0, 1, 0])
        self.assertEqual(result.extra, 'eye')

        # flower win shouldn't count
        self.context.players[0].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('waiting-for-one', self.context, 0, Tile.CIRCLE2))

    def test_waiting_for_edge(self):
        # can wait for a CHAR3 eye or edge, edge should be chosen over eye
        self.context.players[1].hand.free_tiles = [
            Tile.CHAR1, Tile.CHAR2, Tile.CHAR3, Tile.CHAR3, Tile.EAST, Tile.EAST, Tile.EAST
        ]
        result = patterns.match('waiting-for-one', self.context, 1, Tile.CHAR3)
        self.assertEqual(list(result), [1, 0, 1, 1])
        self.assertEqual(result.extra, 'edge')

        # wait for BAMBOO7 edge
        self.context.players[1].hand.free_tiles = [
            Tile.CHAR1, Tile.CHAR1, Tile.CHAR1,
            Tile.BAMBOO8, Tile.BAMBOO9,
            Tile.RED, Tile.RED
        ]
        result = patterns.match('waiting-for-one', self.context, 1, Tile.BAMBOO7)
        self.assertEqual(list(result), [1, 0, 1, 1])
        self.assertEqual(result.extra, 'edge')

        # wait for CIRCLE3 edge
        self.context.players[1].extra.update({
            'win_type': 'melded',
            'chucker': 0
        })
        self.context.players[1].hand.free_tiles = [
            Tile.CIRCLE1, Tile.CIRCLE1, Tile.CIRCLE2, Tile.CIRCLE2, Tile.CIRCLE3,
            Tile.BAMBOO1, Tile.BAMBOO1,
        ]
        result = patterns.match('waiting-for-one', self.context, 1, Tile.CIRCLE3)
        self.assertEqual(list(result), [1, 0, 0, 0])
        self.assertEqual(result.extra, 'edge')

        # flower win shouldn't count
        self.context.players[1].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('waiting-for-one', self.context, 1, Tile.CIRCLE3))

    def test_waiting_for_hole(self):
        # wait for CIRCLE6 eye or hole, hole should be chosen over eye
        self.context.players[2].hand.free_tiles = [
            Tile.CIRCLE5, Tile.CIRCLE6, Tile.CIRCLE6, Tile.CIRCLE7,
            Tile.BAMBOO2, Tile.BAMBOO3, Tile.BAMBOO4,
            Tile.GREEN, Tile.GREEN, Tile.GREEN
        ]
        result = patterns.match('waiting-for-one', self.context, 2, Tile.CIRCLE6)
        self.assertEqual(list(result), [1, 1, 0, 1])
        self.assertEqual(result.extra, 'hole')

        # wait for BAMBOO2
        self.context.players[2].extra.update({
            'win_type': 'melded',
            'chucker': 3
        })
        self.context.players[2].hand.free_tiles = [
            Tile.BAMBOO1, Tile.BAMBOO3, Tile.WHITE, Tile.WHITE
        ]
        result = patterns.match('waiting-for-one', self.context, 2, Tile.BAMBOO2)
        self.assertEqual(list(result), [0, 0, 0, 1])
        self.assertEqual(result.extra, 'hole')

        # flower win shouldn't count
        self.context.players[2].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('waiting-for-one', self.context, 2, Tile.BAMBOO2))

    def test_counter_examples(self):
        # wait for SOUTH and RED
        self.context.players[3].hand.free_tiles = [
            Tile.SOUTH, Tile.SOUTH, Tile.RED, Tile.RED
        ]
        self.assertFalse(patterns.match('waiting-for-one', self.context, 3, Tile.RED))

        # wait for CHAR1 and CHAR2
        self.context.players[3].hand.free_tiles = [
            Tile.CHAR1, Tile.CHAR1, Tile.CHAR2, Tile.CHAR2,
            Tile.CIRCLE5, Tile.CIRCLE5, Tile.CIRCLE5
        ]
        self.assertFalse(patterns.match('waiting-for-one', self.context, 3, Tile.CHAR2))

        # wait for CHAR1 eye, but incoming_tile is not CHAR1
        self.context.players[3].hand.free_tiles = [
            Tile.CHAR1, Tile.CHAR5, Tile.CHAR5, Tile.CHAR5
        ]
        self.assertFalse(patterns.match('waiting-for-one', self.context, 3, Tile.CHAR5))

        # wait for CHAR9 and CIRCLE9
        self.context.players[3].hand.free_tiles = [
            Tile.CHAR9, Tile.CHAR9, Tile.CIRCLE9, Tile.CIRCLE9
        ]
        self.assertFalse(patterns.match('waiting-for-one', self.context, 3, Tile.CHAR9))


class TestRobbedKong(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_robbed_kong(self):
        self.context.players[0].hand.add_free_tile(Tile.CHAR1)
        self.assertFalse(patterns.match('robbed-kong', self.context, 0, Tile.CHAR1))

        self.context.players[0].extra.update({
            'win_type': 'robbed',
            'chucker': 3
        })
        result = patterns.match('robbed-kong', self.context, 0, Tile.CHAR1)
        self.assertEqual(list(result), [0, 0, 0, 1])


class TestKongedOrFlowered(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_konged_or_flowered(self):
        self.context.players[0].hand.add_free_tile(Tile.CHAR1)
        self.assertFalse(patterns.match('konged-or-flowered', self.context, 0, Tile.CHAR1))

        self.context.players[0].extra['konged'] = True
        self.assertFalse(patterns.match('konged-or-flowered', self.context, 0, Tile.CHAR1))

        self.context.players[0].hand.last_tile = Tile.CHAR1

        result = patterns.match('konged-or-flowered', self.context, 0)
        self.assertEqual(list(result), [0, 1, 1, 1])

        self.context.players[0].extra['konged'] = False
        self.assertFalse(patterns.match('konged-or-flowered', self.context, 0, Tile.CHAR1))

        self.context.players[0].extra['flowered'] = True
        result = patterns.match('konged-or-flowered', self.context, 0)
        self.assertEqual(list(result), [0, 1, 1, 1])

        # flower win shouldn't count
        self.context.players[0].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('konged-or-flowered', self.context, 0))


class TestLastTileInWall(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()
        self.context.wall = Wall()
        self.context.settings.tie_wall = 94
        self.context.settings.tie_wall_per_kong = 2

    def test_last_tile_in_wall(self):
        self.context.players[0].hand.add_free_tile(Tile.CHAR1)
        self.context.players[0].hand.fixed_groups += [
            TileGroup([Tile.EAST] * 4, TileGroup.KONG_CONCEALED)
        ]
        self.context.players[1].hand.fixed_groups += [
            TileGroup([Tile.WEST] * 4, TileGroup.KONG_EXPOSED)
        ]
        self.context.players[3].hand.fixed_groups += [
            TileGroup([Tile.BAMBOO7] * 4, TileGroup.KONG_EXPOSED)
        ]
        self.assertFalse(patterns.match('last-tile-in-wall', self.context, 0, Tile.CHAR1))

        while self.context.wall.num_tiles() > 101:
            self.context.wall.draw()

        self.assertFalse(patterns.match('last-tile-in-wall', self.context, 0, Tile.CHAR1))

        self.context.wall.draw()
        self.assertFalse(patterns.match('last-tile-in-wall', self.context, 0, Tile.CHAR1))

        self.context.players[0].hand.last_tile = Tile.CHAR1
        result = patterns.match('last-tile-in-wall', self.context, 0)
        self.assertEqual(list(result), [0, 1, 1, 1])

        # flower win shouldn't count since the last tile doesn't make the player win
        # it's the second last tile (a flower) that makes him win
        self.context.players[0].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('last-tile-in-wall', self.context, 0))


class TestAllMelded(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_all_melded(self):
        self.context.players[1].hand.add_free_tile(Tile.CHAR8)
        self.context.players[1].extra.update({
            'win_type': 'melded',
            'chucker': 0
        })
        result = patterns.match('all-melded', self.context, 1, Tile.CHAR8)
        self.assertEqual(list(result), [1, 0, 0, 0])

        # flower win shouldn't count
        self.context.players[1].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('all-melded', self.context, 1, Tile.CHAR8))

        self.context.players[1].extra['win_type'] = 'melded'
        self.context.players[1].hand.fixed_groups += [
            TileGroup([Tile.BAMBOO1] * 3, TileGroup.PONG),
            TileGroup([Tile.CIRCLE2, Tile.CIRCLE3, Tile.CIRCLE4], TileGroup.CHOW),
            TileGroup([Tile.RED] * 4, TileGroup.KONG_EXPOSED)
        ]
        result = patterns.match('all-melded', self.context, 1, Tile.CHAR8)
        self.assertEqual(list(result), [1, 0, 0, 0])

        # all-melded can't have concealed kong
        self.context.players[1].hand.fixed_groups += [
            TileGroup([Tile.WEST] * 4, TileGroup.KONG_CONCEALED)
        ]
        self.assertFalse(patterns.match('all-melded', self.context, 1, Tile.CHAR8))

        # all-melded can't be self-picked
        self.context.players[1].hand.fixed_groups.pop()
        self.context.players[1].hand.last_tile = Tile.CHAR8
        self.context.players[1].extra.update({
            'win_type': 'self-picked',
            'chucker': None
        })
        self.assertFalse(patterns.match('all-melded', self.context, 1))

    def test_counter_example(self):
        self.context.players[1].hand.free_tiles = [
            Tile.CIRCLE1, Tile.CIRCLE2, Tile.CIRCLE3, Tile.RED
        ]
        self.context.players[1].extra.update({
            'win_type': 'melded',
            'chucker': 0
        })
        self.assertFalse(patterns.match('all-melded', self.context, 1, Tile.RED))


class TestFourKongs(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_four_kongs(self):
        self.context.players[2].hand.add_free_tile(Tile.CHAR1)
        self.context.players[2].hand.fixed_groups += [
            TileGroup([Tile.CHAR2] * 4, TileGroup.KONG_EXPOSED),
            TileGroup([Tile.EAST] * 4, TileGroup.KONG_CONCEALED),
            TileGroup([Tile.GREEN] * 4, TileGroup.KONG_EXPOSED)
        ]
        self.assertFalse(patterns.match('four-kongs', self.context, 2, Tile.CHAR1))

        self.context.players[2].hand.fixed_groups += [
            TileGroup([Tile.BAMBOO3] * 4, TileGroup.KONG_CONCEALED)
        ]
        result = patterns.match('four-kongs', self.context, 2, Tile.CHAR1)
        self.assertEqual(list(result), [1, 1, 0, 1])

        self.context.players[2].extra.update({
            'win_type': 'melded',
            'chucker': 1
        })
        result = patterns.match('four-kongs', self.context, 2, Tile.CHAR1)
        self.assertEqual(list(result), [0, 1, 0, 0])

        # flower win shouldn't count
        self.context.players[2].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('four-kongs', self.context, 2, Tile.CHAR1))


class TestLackASuit(unittest.TestCase):

    def setUp(self):
        self.context = GameContext()

    def test_lack_a_suit(self):
        self.context.players[3].hand.add_free_tiles([
            Tile.CHAR1, Tile.CHAR2, Tile.CHAR3,
            Tile.CHAR7, Tile.CHAR8, Tile.CHAR9,
            Tile.BAMBOO2, Tile.BAMBOO3, Tile.BAMBOO4,
            Tile.BAMBOO6, Tile.BAMBOO7, Tile.BAMBOO8,
            Tile.BAMBOO8
        ])
        self.context.players[3].hand.last_tile = Tile.BAMBOO8

        result = patterns.match('lack-a-suit', self.context, 3)
        self.assertEqual(list(result), [1, 1, 1, 0])

        self.context.players[3].hand.fixed_groups += [
            TileGroup([Tile.CIRCLE4] * 3, TileGroup.PONG)
        ]
        self.assertFalse(patterns.match('lack-a-suit', self.context, 3))

        self.context.players[3].hand.free_tiles = [Tile.BAMBOO4]
        self.context.players[3].hand.last_tile = None

        # flower win shouldn't count
        self.context.players[3].extra['win_type'] = 'flower-won'
        self.assertFalse(patterns.match('lack-a-suit', self.context, 3, Tile.BAMBOO4))

        self.context.players[3].extra.update({
            'win_type': 'melded',
            'chucker': 1
        })
        result = patterns.match('lack-a-suit', self.context, 3, Tile.BAMBOO4)
        self.assertEqual(list(result), [0, 1, 0, 0])

        # lack-a-suit doesn't allow honors
        self.context.players[3].hand.add_free_tiles([Tile.EAST] * 3)
        self.assertFalse(patterns.match('lack-a-suit', self.context, 3, Tile.BAMBOO4))
