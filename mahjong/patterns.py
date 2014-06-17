import collections
import copy

from mahjong import utils
from mahjong.types import Tile, TileGroup


def get(name):
    pattern = _PATTERNS.get(name)
    if not pattern:
        raise KeyError('Pattern `%s` not found' % name)
    return pattern


def match(pattern_name, context, player_idx=None, incoming_tile=None):
    '''
    Match a player to a tile pattern. The available pattern names is listed in
    the ``patterns._PATTERNS``.

    '''
    if player_idx is None:
        player_idx = context.cur_player_idx
        if player_idx is None:
            raise ValueError('Must specify player_idx')
    hand = context.players[player_idx].hand
    if not incoming_tile:
        incoming_tile = hand.last_tile or context.last_discarded()
        if not incoming_tile:
            raise ValueError('Needs an incoming tile')

    pattern = get(pattern_name)
    return pattern.match(context, player_idx, incoming_tile)


def match_all(context, player_idx):
    '''
    Match all patterns listed in ``context.settings.patterns_score``. Return
    the matched patterns as a dictionary where keys are pattern names and
    values are MatchResults.

    '''
    excluded_pattern_names = set()
    results = {}
    for name, __ in context.settings.patterns_score.iteritems():
        # if the pattern has been excluded, it means the pattern won't match anyway
        # so no need to check it
        if name in excluded_pattern_names:
            continue

        match_result = match(name, context, player_idx)
        if match_result:
            results[name] = match_result

            # add excluded patterns into the set
            pattern = get(name)
            if pattern.excludes:
                for excluded_name in pattern.excludes:
                    excluded_pattern_names.add(excluded_name)

    def subtract_implied(pattern1, match_result1, pattern_name2, match_result2):
        for i in xrange(0, 4):
            mult = match_result1.get(i)
            if mult > 0:
                match_result2.set(i, 0)

    def subtract_intersected(pattern1, match_result1, pattern_name2, match_result2):
        result = pattern1.intersect(match_result1, pattern_name2, match_result2)
        for i in xrange(0, 4):
            mult = result.get(i)
            match_result2.set(i, mult)

    # filter results according to Pattern.implies and Pattern.intersects
    results = _filter_match_results(results, 'implies', subtract_implied)
    results = _filter_match_results(results, 'intersects', subtract_intersected)

    return results


class MatchResult(object):
    '''
    A MatchResult is essentially an array which has four elements:
    [S0, S1, S2, S3], where Si is a score multiplier that player i should pay
    the winner. Also, you can store any extra data in ``MatchResult.extra``.

    '''
    def __init__(self, player_idx=None, multiplier=None, extra=None):
        self._multipliers = [0, 0, 0, 0]
        self.extra = extra
        if not (player_idx is None or multiplier is None):
            self.set(player_idx, multiplier)

    def __nonzero__(self):
        return any(self._multipliers)

    def __iter__(self):
        return iter(self._multipliers)

    def __eq__(self, other):
        return self._multipliers == other._multipliers and self.extra == other.extra

    def __repr__(self):
        return '(%s, %s)' % (self._multipliers, self.extra)

    def set(self, player_idx, multiplier):
        try:
            # player_idx is iterable
            for i in player_idx:
                self._multipliers[i] = multiplier
        except TypeError:
            # if player_idx isn't iterable, it's a single value
            self._multipliers[player_idx] = multiplier

    def get(self, player_idx):
        return self._multipliers[player_idx]

    def clone(self):
        result = MatchResult()
        result._multipliers = copy.copy(self._multipliers)
        result.extra = copy.copy(self.extra)
        return result


class Pattern(object):
    '''
    This class is used for pattern matching when scoring and determine a
    winning hand.

    Subclasses of Pattern must implement ``match()`` method.

    In your subclass, you can describe the relationships between the pattern
    you're writing and the other patterns with these fields:

    * ``Pattern.implies``: A implies B <=> If A is true, B is true.

    * ``Pattern.excludes``: A excludes B <=> No intersection between A and B.

    * ``Pattern.intersects``: Normally, we can simply add the scores together
      if the two patterns intersects with each other. But there're exceptions.
      Use this field and ``Pattern.intersect()`` to deal with it.

    '''
    implies = None
    excludes = None
    intersects = None

    def match(self, context, player_idx, incoming_tile):
        '''
        Return a MatchResult. A MatchResult is essentially an array which has
        four elements: [S0, S1, S2, S3], where Si is a score multiplier that
        player i should pay the winner (i.e., player_idx).

        For example, if this pattern is set to be counted as x points, the
        returned value [0, 0, 2, 1] means player 2 and 3 should pay the
        winner 2x and x points, respectively.

        '''
        raise NotImplementedError

    def intersect(self, match_result1, pattern_name2, match_result2):
        '''
        This method computes intersection between this pattern and another
        pattern. Subclass should implement this method if it has
        ``intersects`` field specified.

        :param match_result1: MatchResult of this pattern.
        :param pattern_name2: The other pattern name that was in
                              ``Pattern.intersects``.
        :param match_result2: MatchResult of the other pattern.

        :returns: MatchResult of intersection.

        '''
        raise NotImplementedError

    def default_result(self, context, player_idx, multiplier=1, extra=None):
        winner = context.players[player_idx]
        chucker = winner.extra.get('chucker')
        if chucker is not None:
            return MatchResult(chucker, multiplier, extra)
        return self.result_other_players(context, player_idx, multiplier, extra)

    def result_other_players(self, context, player_idx, multiplier=1, extra=None):
        chuckers = []
        for i in xrange(0, 4):
            if i != player_idx:
                chuckers.append(i)
        return MatchResult(chuckers, multiplier, extra)


def check_flower_win(match_method):
    '''
    Normally, the input player that passed into ``Pattern.match()`` has a
    winning hand. The only exception is **flower win** where the player holds
    eight flowers. If you need to filter out this special winning case,
    decorate ``Pattern.match()`` with this.

    '''
    def wrapper(self, context, player_idx, incoming_tile):
        # if player wins with flowers (not a normal winning hand),
        # Player.extra['win_type'] will be marked as true
        if context.players[player_idx].extra.get('win_type') == 'flower-won':
            return MatchResult()
        return match_method(self, context, player_idx, incoming_tile)
    return wrapper


class Dealer(Pattern):
    '''
    Is the dealer a winner or a chucker?

    '''
    def match(self, context, player_idx, incoming_tile):
        # dealer wins or chucks
        chucker = context.players[player_idx].extra.get('chucker')
        self_picked = chucker is None
        if self_picked:
            if context.dealer == player_idx:
                return self.default_result(context, player_idx)
            return MatchResult(context.dealer, 1)
        elif context.dealer == player_idx or chucker == context.dealer:
            return MatchResult(chucker, 1)

        return MatchResult()


class DealerDefended(Dealer):
    '''
    Does the dealer win or chuck? If yes, how many times did he defend his
    dealer position?

    '''
    def match(self, context, player_idx, incoming_tile):
        result = super(DealerDefended, self).match(context, player_idx, incoming_tile)
        if result:
            for i in xrange(0, 4):
                new_mult = result.get(i) * context.dealer_defended
                result.set(i, new_mult)

        return result


class DeclaredReady(Pattern):
    '''
    Did the player declare ready?

    '''
    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        player = context.players[player_idx]
        if player.extra.get('declared_ready'):
            return self.default_result(context, player_idx)

        return MatchResult()


class WindSeat(Pattern):
    '''
    3+ wind tiles that matches the seat.

    '''
    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        seat_wind = Tile.WINDS[player_idx]
        hand = context.players[player_idx].hand
        if hand.count(seat_wind, fixed_groups=True) > 2:
            return self.default_result(context, player_idx, extra=seat_wind)

        return MatchResult()


class WindRound(Pattern):
    '''
    3+ wind tiles that matches the round.

    '''
    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        round_wind = Tile.WINDS[context.round % 4]
        hand = context.players[player_idx].hand
        if hand.count(round_wind, fixed_groups=True) > 2:
            return self.default_result(context, player_idx, extra=round_wind)

        return MatchResult()


class Dragons(Pattern):
    '''
    3+ same suit of dragons.

    '''
    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        dragons = (Tile.RED, Tile.GREEN, Tile.WHITE)
        hand = context.players[player_idx].hand.clone()
        hand.last_tile = incoming_tile

        multiplier = 0
        extra = []
        for dragon in dragons:
            if hand.count(dragon, fixed_groups=True) > 2:
                multiplier += 1
                extra.append(dragon)

        if multiplier > 0:
            return self.default_result(context, player_idx, multiplier, extra)

        return MatchResult()


class FlowerSeat(Pattern):
    '''
    A flower that matches the seat.

    '''
    excludes = ('all-sequences',)

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        flowers = (Tile.PLUM, Tile.ORCHID, Tile.BAMBOO, Tile.CHRYSANTH)
        seasons = (Tile.SPRING, Tile.SUMMER, Tile.AUTUMN, Tile.WINTER)
        seat_flower = flowers[player_idx]
        seat_season = seasons[player_idx]
        hand = context.players[player_idx].hand
        multiplier = 0
        extra = []
        if hand.contains(seat_flower, free_tiles=False, flowers=True):
            multiplier += 1
            extra.append(seat_flower)
        if hand.contains(seat_season, free_tiles=False, flowers=True):
            multiplier += 1
            extra.append(seat_season)

        if multiplier > 0:
            return self.default_result(context, player_idx, multiplier, extra)

        return MatchResult()


class FourFlowers(Pattern):
    '''
    Has (PLUM, ORCHID, BAMBOO, CHRYSANTH) or (SPRING, SUMMER, AUTUMN, WINTER).

    '''
    excludes = ('all-sequences',)
    intersects = ('flower-seat',)

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        flowers = (Tile.PLUM, Tile.ORCHID, Tile.BAMBOO, Tile.CHRYSANTH)
        seasons = (Tile.SPRING, Tile.SUMMER, Tile.AUTUMN, Tile.WINTER)
        hand = context.players[player_idx].hand

        has_all_flowers = self._has_all(hand, flowers)
        has_all_seasons = self._has_all(hand, seasons)

        multiplier = 0
        extra = []
        if has_all_flowers:
            multiplier += 1
            extra.append('flowers')
        if has_all_seasons:
            multiplier += 1
            extra.append('seasons')

        if multiplier > 0:
            return self.default_result(context, player_idx, multiplier, extra)

        return MatchResult()

    def intersect(self, match_result1, pattern_name2, match_result2):
        result = MatchResult()

        if pattern_name2 == 'flower-seat':
            for i in xrange(0, 4):
                mult1 = match_result1.get(i)
                mult2 = match_result2.get(i)
                result.set(i, max(mult2 - mult1, 0))

                # edit match_result2.extra
                if match_result2.extra:
                    if 'flowers' in match_result1.extra:
                        match_result2.extra = filter(lambda x: x.is_season(),
                                                     match_result2.extra)
                    if 'seasons' in match_result1.extra:
                        match_result2.extra = filter(lambda x: x.is_special_flower(),
                                                     match_result2.extra)
                    if not match_result2.extra:
                        match_result2.extra = None

        return result

    def _has_all(self, hand, tiles):
        for tile in tiles:
            if not hand.contains(tile, free_tiles=False, flowers=True):
                return False
        return True


class ConcealedTriplets(Pattern):

    def __init__(self, num_triplets):
        super(ConcealedTriplets, self).__init__()
        self.num_triplets = num_triplets

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        # copy hand, incoming_tile discarded by others is not considered concealed,
        # so it's not included here
        hand = context.player(player_idx).hand.clone()
        if hand.last_tile:
            incoming_tile = None
        hand.move_last_tile()

        num_concealed_kongs = hand.num_kongs(exposed=False)
        if num_concealed_kongs >= self.num_triplets:
            return self.default_result(context, player_idx)

        num_triplets_needed = self.num_triplets - num_concealed_kongs
        if self._has_triplets(hand, num_triplets_needed, incoming_tile):
            return self.default_result(context, player_idx)

        return MatchResult()

    def _has_triplets(self, hand, num_triplets, incoming_tile):
        candidates = self._triplet_candidates(hand)
        orig_tiles = hand.free_tiles
        triplet_count = 0

        for tile in candidates:
            idx = utils.index(hand.free_tiles, tile)
            prev_tiles = hand.free_tiles
            hand.free_tiles = hand.free_tiles[0:idx] + hand.free_tiles[idx + 3:]

            print '%d - %s' % (triplet_count, hand)

            if hand.can_win(incoming_tile):
                triplet_count += 1
                if triplet_count == num_triplets:
                    break
            else:
                hand.free_tiles = prev_tiles

        hand.free_tiles = orig_tiles
        return triplet_count == num_triplets

    def _triplet_candidates(self, hand):
        result = []
        num_tiles = len(hand.free_tiles)
        i = 0
        while i < num_tiles - 2:
            if hand.free_tiles[i] == hand.free_tiles[i + 2]:
                result.append(hand.free_tiles[i])
                i += 3
            else:
                i += 1
        return result


class ThreeConcealedTriplets(ConcealedTriplets):

    def __init__(self):
        super(ThreeConcealedTriplets, self).__init__(3)


class FourConcealedTriplets(ConcealedTriplets):

    implies = ('three-concealed-triplets',)

    def __init__(self):
        super(FourConcealedTriplets, self).__init__(4)


class FiveConcealedTriplets(ConcealedTriplets):

    implies = ('three-concealed-triplets', 'four-concealed-triplets')

    def __init__(self):
        super(FiveConcealedTriplets, self).__init__(5)


class AllPongs(Pattern):
    '''
    Consists of pongs, triplets, and a pair. No chows and sequences.

    '''
    excludes = ('all-sequences',)

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        hand = context.players[player_idx].hand.clone()
        hand.add_free_tile(incoming_tile)
        hand.last_tile = None

        # can't have chows
        for group in hand.fixed_groups:
            if group.group_type == TileGroup.CHOW:
                return MatchResult()

        # can't have sequences
        num_tiles = len(hand.free_tiles)
        i = 0
        last_idx = 0
        while i < num_tiles - 1:
            if hand.free_tiles[i] != hand.free_tiles[i + 1]:
                if i - last_idx < 2:
                    return MatchResult()
                last_idx = i
            i += 1

        return self.default_result(context, player_idx)


class PurelyConcealedSelfPicked(Pattern):
    '''
    Purely-concealed and self-picked.

    '''
    excludes = ('all-melded', 'all-sequences', 'robbed-kong', 'four-kongs')
    implies = ('purely-concealed', 'self-picked')

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        hand = context.players[player_idx].hand
        self_picked = self._self_picked(hand)
        purely_concealed = self._purely_concealed(hand)
        if self_picked and purely_concealed:
            return self.result_other_players(context, player_idx)

        return MatchResult()

    def _purely_concealed(self, hand):
        for group in hand.fixed_groups:
            if group.group_type != TileGroup.KONG_CONCEALED:
                return False
        return True

    def _self_picked(self, hand):
        return bool(hand.last_tile)


class PurelyConcealed(PurelyConcealedSelfPicked):
    '''
    No exposed kongs, pongs, and chows.

    '''
    excludes = ('all-melded', 'four-kongs')
    implies = None

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        hand = context.players[player_idx].hand
        if self._purely_concealed(hand):
            return self.default_result(context, player_idx)

        return MatchResult()


class SelfPicked(PurelyConcealedSelfPicked):
    '''
    Won by self-picking.

    '''
    excludes = ('all-melded', 'all-sequences', 'robbed-kong')
    implies = None

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        hand = context.players[player_idx].hand
        if self._self_picked(hand):
            return self.result_other_players(context, player_idx)

        return MatchResult()


class SevenFlowers(Pattern):
    '''
    A hand that has seven flowers already, and has another flower from
    someone else.

    '''
    implies = ('four-flowers', 'flower-seat')
    excludes = ('eight-flowers', 'all-sequences')

    def match(self, context, player_idx, incoming_tile):
        player = context.players[player_idx]
        hand = player.hand
        self_picked = (incoming_tile == hand.last_tile)

        # for determining if it wins (algo.can_win())
        if not self_picked and len(hand.flowers) == 7 and incoming_tile.is_general_flower():
            # assume it's current player who chucks
            return MatchResult(context.cur_player_idx, 1)

        # for scoring (algo.score())
        chucker = context.extra.get('flower_chucker')
        if len(hand.flowers) > 7 and chucker is not None:
            return MatchResult(chucker, 1)

        return MatchResult()


class EightFlowers(Pattern):
    '''
    A hand that has eight flowers.

    '''
    implies = ('four-flowers', 'flower-seat')
    excludes = ('seven-flowers', 'all-sequences')

    def match(self, context, player_idx, incoming_tile):
        player = context.players[player_idx]
        hand = player.hand

        # for determining if it wins
        self_picked = (incoming_tile == hand.last_tile)
        if self_picked and len(hand.flowers) == 7 and incoming_tile.is_general_flower():
            return self.result_other_players(context, player_idx)

        # for scoring
        chucker = context.extra.get('flower_chucker')
        if len(hand.flowers) > 7 and chucker is None:
            return self.result_other_players(context, player_idx)

        return MatchResult()


class FlowerWinAfterDealing(Pattern):
    '''
    Get seven-flowers or eight-flowers before discarding the first tile.

    '''
    def match(self, context, player_idx, incoming_tile):
        player = context.players[player_idx]
        if len(player.hand.flowers) > 7 and not player.discarded:
            chucker = context.extra.get('flower_chucker')
            if chucker is None:
                # eight-flowers
                return self.result_other_players(context, player_idx)

            # seven flowers
            return MatchResult(chucker, 1)

        return MatchResult()


class HeavenWin(Pattern):
    '''
    The dealer wins without discarding any tile.

    '''
    implies = ('dealer', 'self-picked', 'purely-concealed', 'purely-concealed-self-picked')
    excludes = ('declared-ready', 'earth-win', 'human-win', 'heaven-ready', 'earth-ready')

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        if player_idx == context.dealer and not context.discarded_pool:
            return self.result_other_players(context, player_idx)

        return MatchResult()


class EarthWin(Pattern):
    '''
    A non-dealer player wins without discarding a tile.

    '''
    implies = ('self-picked', 'purely-concealed', 'purely-concealed-self-picked')
    excludes = ('declared-ready', 'heaven-win', 'human-win', 'heaven-ready', 'earth-ready')

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        player = context.players[player_idx]
        self_picked = incoming_tile == player.hand.last_tile
        if self_picked and player_idx != context.dealer and not player.discarded:
            return self.result_other_players(context, player_idx)

        return MatchResult()


class HumanWin(Pattern):
    '''
    Wins by taking someone else's first discarded tile.

    '''
    excludes = ('declared-ready', 'self-picked', 'heaven-win', 'earth-win', 'heaven-ready',
                'earth-ready')

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        player = context.players[player_idx]
        chucker = player.extra.get('chucker')
        if chucker is not None:
            if len(context.players[chucker].discarded) == 1:
                return MatchResult(chucker, 1)

        return MatchResult()


class HeavenReady(Pattern):

    implies = ('dealer', 'declared-ready',)
    excludes = ('heaven-win', 'earth-win', 'human-win', 'earth-ready')

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        player = context.players[player_idx]
        if player_idx == context.dealer and player.extra.get('immediate_ready'):
            return self.default_result(context, player_idx)

        return MatchResult()


class EarthReady(Pattern):

    implies = ('declared-ready',)
    excludes = ('heaven-win', 'earth-win', 'human-win', 'heaven-ready')

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        player = context.players[player_idx]
        if player_idx != context.dealer and player.extra.get('immediate_ready'):
            return self.default_result(context, player_idx)

        return MatchResult()


class BigHonors(Pattern):

    def __init__(self, honors):
        super(BigHonors, self).__init__()
        self.honors = honors

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        hand = context.players[player_idx].hand.clone()
        hand.last_tile = incoming_tile
        for honor in self.honors:
            if hand.count(honor, fixed_groups=True) < 3:
                return MatchResult()

        return self.default_result(context, player_idx)


class SmallHonors(Pattern):

    def __init__(self, honors):
        super(SmallHonors, self).__init__()
        self.honors = honors

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        pair_count = 0
        hand = context.players[player_idx].hand.clone()
        hand.last_tile = incoming_tile
        for honor in self.honors:
            count = hand.count(honor, fixed_groups=True)
            if count < 3:
                if count == 2:
                    if pair_count > 0:
                        return MatchResult()
                    pair_count += 1
                else:
                    return MatchResult()

        return self.default_result(context, player_idx)


class BigFourWinds(BigHonors):
    '''
    Four triplets of winds.

    '''
    implies = ('small-four-winds', 'wind-seat', 'wind-round')

    def __init__(self):
        super(BigFourWinds, self).__init__(Tile.WINDS)


class SmallFourWinds(SmallHonors):
    '''
    Three triplets of winds plus a pair of winds.

    '''
    def __init__(self):
        super(SmallFourWinds, self).__init__(Tile.WINDS)


class BigThreeDragons(BigHonors):
    '''
    Three triplets of dragons.

    '''
    implies = ('small-three-dragons', 'dragons')

    def __init__(self):
        super(BigThreeDragons, self).__init__(Tile.DRAGONS)


class SmallThreeDragons(SmallHonors):
    '''
    Two triplets of dragons plus a pair of dragons.

    '''
    implies = ('dragons',)

    def __init__(self):
        super(SmallThreeDragons, self).__init__(Tile.DRAGONS)


class SuitPattern(Pattern):

    def iterate(self, hand, last_tile=True, free_tiles=True, fixed_groups=True):
        if last_tile and hand.last_tile:
            yield hand.last_tile

        if free_tiles:
            for tile in hand.free_tiles:
                yield tile

        if fixed_groups:
            for group in hand.fixed_groups:
                for tile in group.tiles:
                    yield tile


class AllHonors(SuitPattern):

    implies = ('all-pongs',)

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        hand = context.players[player_idx].hand.clone()
        hand.last_tile = incoming_tile

        for tile in self.iterate(hand):
            if not tile.is_honor():
                return MatchResult()

        return self.default_result(context, player_idx)


class SameSuit(SuitPattern):
    '''
    Same suit but no honors.

    '''
    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        hand = context.players[player_idx].hand

        if incoming_tile.is_honor():
            return MatchResult()

        for tile in self.iterate(hand):
            if tile.suit != incoming_tile.suit:
                return MatchResult()

        return self.default_result(context, player_idx)


class MixASuit(SuitPattern):
    '''
    Honors and a numeric suit of tiles.

    '''
    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        hand = context.players[player_idx].hand.clone()
        hand.last_tile = incoming_tile

        if not self._has_honor(hand):
            return MatchResult()

        suit = self._find_non_honor_suit(hand)
        if not suit:
            return MatchResult()

        for tile in self.iterate(hand):
            if not (tile.suit == suit or tile.is_honor()):
                return MatchResult()

        return self.default_result(context, player_idx)

    def _has_honor(self, hand):
        if hand.last_tile.is_honor():
            return True
        if hand.free_tiles and hand.free_tiles[-1].is_honor():
            return True
        for group in hand.fixed_groups:
            if group.tiles[0].is_honor():
                return True
        return False

    def _find_non_honor_suit(self, hand):
        for tile in self.iterate(hand):
            if not tile.is_honor():
                return tile.suit
        return None


class AllSequences(Pattern):
    '''
    Sequences and a pair. Plus these conditions:
    * Not self-picked
    * No flowers
    * No honors
    * More than 1 waiting tile

    '''
    excludes = ('three-concealed-triplets', 'four-concealed-triplets',
                'five-concealed-triplets', 'all-pongs', 'waiting-for-one',
                'self-picked', 'flower-seat', 'four-flowers', 'seven-flowers',
                'eight-flowers')

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        player = context.players[player_idx]

        # check if it's self-picked, has flower, or has honor
        self_picked = bool(player.hand.last_tile)
        if self_picked or player.hand.flowers or self._has_honor(player.hand):
            return MatchResult()

        # check if groups are sequences (chows)
        for group in player.hand.fixed_groups:
            if group.group_type != TileGroup.CHOW:
                return MatchResult()

        hand = player.hand.clone()
        hand.add_free_tile(incoming_tile)

        # check if the hand can be grouped into sequences and a pair
        if not self._can_be_grouped_into_seqs_and_pair(hand.free_tiles):
            return MatchResult()

        # check if there're more than one waiting tile
        if len(player.hand.waiting_tiles()) < 2:
            return MatchResult()

        chucker = player.extra.get('chucker')
        if chucker is None:
            return MatchResult()

        return MatchResult(chucker, 1)

    def _has_honor(self, hand):
        if hand.free_tiles[-1].is_honor():
            return True
        for group in hand.fixed_groups:
            if group.tiles[0].is_honor():
                return True
        return False

    def _can_be_grouped_into_seqs_and_pair(self, tiles):
        pairs = self._find_pairs(tiles)
        if not pairs:
            return False

        # remove pair and see if rest of tiles can be grouped into sequences
        for pair_idx in pairs:
            tiles_no_pair = self._remove_pair(tiles, pair_idx)
            if self._all_sequences(tiles_no_pair):
                return True

        return False

    def _all_sequences(self, tiles):
        if not tiles:
            return True

        tile_queue = collections.deque(tiles)
        while True:
            try:
                tile0 = tile_queue.popleft()
            except IndexError:
                break
            tile1 = Tile.ALL.get(tile0.tile_id + 1)
            tile2 = Tile.ALL.get(tile0.tile_id + 2)
            if not (tile1 and tile2):
                return False

            try:
                tile_queue.remove(tile1)
                tile_queue.remove(tile2)
            except ValueError:
                return False

        return True

    def _remove_pair(self, tiles, pair_idx):
        result = []
        num_tiles = len(tiles)
        for i in xrange(0, num_tiles):
            if (i - pair_idx) not in (0, 1):
                result.append(tiles[i])
        return result

    def _find_pairs(self, tiles):
        pairs = []
        num_tiles = len(tiles)
        for i in xrange(0, num_tiles - 1):
            if tiles[i] == tiles[i + 1]:
                pairs.append(i)
        return pairs


class WaitingForOne(Pattern):
    '''
    Waits for one tile only. The waiting tile can be categorized into:
    * Hole: [1, 3, 5, 5] waits for 2
    * Edge: [1, 2, 5, 5] waits for 3
    * Eye: [1, 2, 3, 5] waits for 5

    '''
    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        hand = context.players[player_idx].hand
        waiting_tiles = hand.waiting_tiles()
        if len(waiting_tiles) != 1:
            return MatchResult()

        tile = waiting_tiles[0]
        if tile != incoming_tile:
            return MatchResult()

        if tile.is_honor():
            extra = 'eye'
        elif self._is_edge(hand, tile):
            extra = 'edge'
        elif self._is_hole(hand, tile):
            extra = 'hole'
        else:
            extra = 'eye'

        return self.default_result(context, player_idx, extra=extra)

    def _is_edge(self, hand, tile):
        if tile.rank == 7:
            tile1 = Tile.ALL.get(tile.tile_id + 1)
            tile2 = Tile.ALL.get(tile.tile_id + 2)
        elif tile.rank == 3:
            tile1 = Tile.ALL.get(tile.tile_id - 2)
            tile2 = Tile.ALL.get(tile.tile_id - 1)
        else:
            return False

        return self._remove_and_can_win(hand, (tile1, tile2))

    def _is_hole(self, hand, tile):
        if tile.rank in (1, 9):
            return False

        tile1 = Tile.ALL.get(tile.tile_id - 1)
        tile2 = Tile.ALL.get(tile.tile_id + 1)

        return self._remove_and_can_win(hand, (tile1, tile2))

    def _remove_and_can_win(self, hand, tiles_to_be_removed):
        hand = hand.clone()

        for tile in tiles_to_be_removed:
            idx = utils.index(hand.free_tiles, tile)
            if idx < 0:
                return False
            del hand.free_tiles[idx]

        return hand.can_win()


class RobbedKong(Pattern):

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        player = context.players[player_idx]
        if player.extra.get('win_type') == 'robbed':
            return self.default_result(context, player_idx)

        return MatchResult()


class KongedOrFlowered(Pattern):

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        player = context.players[player_idx]
        self_picked = bool(player.hand.last_tile)
        if self_picked and player.extra.get('konged') or player.extra.get('flowered'):
            return self.result_other_players(context, player_idx)

        return MatchResult()


class LastTileInWall(Pattern):

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        player = context.players[player_idx]
        self_picked = bool(player.hand.last_tile)
        if self_picked and context.is_tie(cur_state=False, four_waiting=False,
                                          four_kongs=False, four_winds=False):
            return self.result_other_players(context, player_idx)

        return MatchResult()


class AllMelded(Pattern):

    excludes = ('self-picked', 'purely-concealed', 'purely-concealed-self-picked')

    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        player = context.players[player_idx]
        self_picked = bool(player.hand.last_tile)
        if not self_picked and len(player.hand.free_tiles) == 1 and \
           not self._has_concealed_kong(player.hand):
            return self.default_result(context, player_idx)

        return MatchResult()

    def _has_concealed_kong(self, hand):
        for group in hand.fixed_groups:
            if group.group_type == TileGroup.KONG_CONCEALED:
                return True
        return False


class FourKongs(Pattern):
    '''
    A hand that has four kongs.

    '''
    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        hand = context.players[player_idx].hand
        num_kongs = hand.num_kongs()
        if num_kongs > 3:
            return self.default_result(context, player_idx)

        # for 4-kong winning
        # TODO: remove this
        if num_kongs == 3:
            if hand.count(incoming_tile, last_tile=False) > 2:
                return self.default_result(context, player_idx)
            if hand.last_tile == incoming_tile:
                for group in hand.fixed_groups:
                    if group.group_type == TileGroup.PONG and group.tiles[0] == incoming_tile:
                        return self.default_result(context, player_idx)

        return MatchResult()


class LackASuit(Pattern):
    '''
    No honors and lack of a numeric suit.

    '''
    @check_flower_win
    def match(self, context, player_idx, incoming_tile):
        suit_counts = {
            'char': 0,
            'circle': 0,
            'bamboo': 0,
            'honor': 0,
            'flower': 0
        }
        hand = context.players[player_idx].hand
        for tile in hand.free_tiles:
            suit = self._suit_name(tile)
            suit_counts[suit] += 1

        for group in hand.fixed_groups:
            suit = self._suit_name(group.tiles[0])
            suit_counts[suit] += 1

        if suit_counts.get('honor') > 0:
            return MatchResult()

        numeric_count = 0
        if suit_counts.get('char') > 0:
            numeric_count += 1
        if suit_counts.get('circle') > 0:
            numeric_count += 1
        if suit_counts.get('bamboo') > 0:
            numeric_count += 1
        if numeric_count == 2:
            return self.default_result(context, player_idx)

        return MatchResult()

    def _suit_name(self, tile):
        table = {
            Tile.SUIT_CHAR: 'char',
            Tile.SUIT_CIRCLE: 'circle',
            Tile.SUIT_BAMBOO: 'bamboo',
            Tile.SUIT_WIND: 'honor',
            Tile.SUIT_DRAGON: 'honor',
            Tile.SUIT_FLOWER: 'flower',
            Tile.SUIT_SEASON: 'flower'
        }
        return table.get(tile.suit)


# Pattern table
_PATTERNS = {
    # Taiwanese 16
    'dealer': Dealer(),
    'dealer-defended': DealerDefended(),
    'declared-ready': DeclaredReady(),
    'wind-seat': WindSeat(),
    'wind-round': WindRound(),
    'dragons': Dragons(),
    'flower-seat': FlowerSeat(),
    'four-flowers': FourFlowers(),
    'three-concealed-triplets': ThreeConcealedTriplets(),
    'four-concealed-triplets': FourConcealedTriplets(),
    'five-concealed-triplets': FiveConcealedTriplets(),
    'all-pongs': AllPongs(),
    'purely-concealed': PurelyConcealed(),
    'self-picked': SelfPicked(),
    'seven-flowers': SevenFlowers(),
    'eight-flowers': EightFlowers(),
    'flower-win-after-dealing': FlowerWinAfterDealing(),
    'heaven-win': HeavenWin(),
    'earth-win': EarthWin(),
    'human-win': HumanWin(),
    'heaven-ready': HeavenReady(),
    'earth-ready': EarthReady(),
    'big-four-winds': BigFourWinds(),
    'small-four-winds': SmallFourWinds(),
    'big-three-dragons': BigThreeDragons(),
    'small-three-dragons': SmallThreeDragons(),
    'all-honors': AllHonors(),
    'same-suit': SameSuit(),
    'mix-a-suit': MixASuit(),
    'all-sequences': AllSequences(),
    'waiting-for-one': WaitingForOne(),
    'robbed-kong': RobbedKong(),
    'konged-or-flowered': KongedOrFlowered(),
    'last-tile-in-wall': LastTileInWall(),
    'all-melded': AllMelded(),
    'purely-concealed-self-picked': PurelyConcealedSelfPicked(),

    'four-kongs': FourKongs(),
    'lack-a-suit': LackASuit()
}


# Add more exclusion such that:
# If pattern A excludes B, B excludes A as well
def _add_auto_excludes():
    for name, pattern in _PATTERNS.items():
        if pattern.excludes:
            for other_name in pattern.excludes:
                other_pattern = get(other_name)
                if other_pattern.excludes is None:
                    other_pattern.excludes = tuple()
                if name not in other_pattern.excludes:
                    other_pattern.excludes += (name,)

_add_auto_excludes()


def _copy_match_results(match_results):
    result = {}
    for name, match_result in match_results.iteritems():
        result[name] = match_result.clone()
    return result


def _filter_match_results(match_results, attr_name, subtract_func):
    results = _copy_match_results(match_results)

    for name, match_result in match_results.iteritems():
        pattern = get(name)
        other_names = getattr(pattern, attr_name)
        if other_names:
            for other_name in other_names:
                match_result2 = results.get(other_name)
                if match_result2:
                    subtract_func(pattern, match_result, other_name, match_result2)
                    if not match_result2:
                        results.pop(other_name, None)

    return results
