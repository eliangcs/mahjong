import bisect

from mahjong import bots, patterns, scoring
from mahjong.types import Tile


def can_win(context, player_idx=None, incoming_tile=None):
    '''
    Return if a player can win.

    Unlike Hand.can_win(), this function does extra checking for special
    winning patterns and winning restrictions (filters) in GameSettings.

    '''
    player_idx = _get_player_index(context, player_idx)
    incoming_tile = _get_incoming_tile(context, player_idx, incoming_tile)

    player = context.players[player_idx]
    hand = player.hand

    # if player declared ready, there should be waiting tiles cached in player.extra already
    # so no need to call costly Hand.can_win()
    if player.extra.get('declared_ready'):
        waiting_tiles = player.extra.get('waiting_tiles')
        if waiting_tiles and incoming_tile in waiting_tiles:
            return True

    # check if player is in water penalty
    if context.settings.water:
        waiting_tiles = player.extra.get('water')
        if waiting_tiles and incoming_tile in waiting_tiles:
            return False

    # general winning pattern
    if hand.can_win(incoming_tile):
        all_matched = True
        for pattern_name in context.settings.patterns_win_filter:
            all_matched = patterns.match(pattern_name, context, player_idx, incoming_tile)
            if not all_matched:
                break
        if all_matched:
            return True

    # special winning patterns
    for pattern_name in context.settings.patterns_win:
        if patterns.match(pattern_name, context, player_idx, incoming_tile):
            return True

    return False


def can_flower_win(context, player_idx=None, incoming_tile=None):
    '''
    Return if a player can win with a flower.

    Actually, this function can be replaced with algo.can_win(), but it only
    checks for flower winning, which is much faster.

    '''
    player_idx = _get_player_index(context, player_idx)
    incoming_tile = _get_incoming_tile(context, player_idx, incoming_tile)

    if not incoming_tile.is_general_flower():
        return False

    for pattern_name in ('seven-flowers', 'eight-flowers'):
        if pattern_name in context.settings.patterns_win:
            if patterns.match(pattern_name, context, player_idx, incoming_tile):
                return True

    return False


def waiting_tiles(context, player_idx=None):
    '''
    Return a list of tiles that makes a player a winning hand.

    Unlike Hand.waiting_tiles(), this function covers special winning patterns
    and winning restrictions (filters) in GameSettings. This function is quite
    time-expensive. Use it with caution.

    '''
    if player_idx is None:
        player_idx = context.cur_player_idx

    player = context.players[player_idx]
    if player.extra.get('declared_ready'):
        waiting_tiles = player.extra.get('waiting_tiles')
        if waiting_tiles is not None:
            return waiting_tiles

    tiles = []
    for tile in Tile.ALL.itervalues():
        if can_win(context, player_idx, tile):
            bisect.insort(tiles, tile)
    return tiles


def ready(context, player_idx=None):
    '''
    Is a player has a ready hand?

    Unlike Hand.ready(), this function covers special winning patterns and
    winning restrictions (filters) in GameSettings. This function is quite
    time-expensive. Use it with caution.

    '''
    for tile in Tile.ALL.itervalues():
        if can_win(context, player_idx, tile):
            return True
    return False


def select_melders(viable_decisions, player_decisions, base_offset=0):
    '''
    Given a table of viable decisions that all players can make, this function
    selects top-priority players and their decisions.

    Example:

        viable_decisions = [
            None,                    # player 0 can't do anything
            ['chow', 'skip'],        # player 1 can chow
            ['win', 'pong', 'skip'], # player 2 can win and pong
            ['win', 'skip']          # player 3 can win
        ]
        player_decisions = [
            None,
            'chow',
            'win',
            'win'
        ]

        melders = _select_melder(viable_decisions, player_decisions)
        assert melders == [(2, 'win'), (3, 'win')]

    Notice that the input arrays don't have to be length of 4. As long as they
    have the same length, this function will work.

    '''
    result = []
    num_players = len(player_decisions)

    # multiple winners could be allowed,
    # so we need add all winners into result
    for i in xrange(0, num_players):
        player_idx = (base_offset + i) % num_players
        player_viable = viable_decisions[player_idx]
        if player_viable and 'win' in player_viable:
            player_decision = player_decisions[player_idx]
            if player_decision == 'win':
                result.append((player_idx, 'win'))
            elif player_decision not in player_viable:
                # player i hasn't make a decision,
                # this returned value indicates we need to wait for him
                return [(player_idx, None)]

    # if anyone wants to win, no need to check kong, pong, chow
    if result:
        return result

    # there can be only one kong, pong, or chow
    for decision in ('kong', 'pong', 'chow'):
        for i in xrange(0, num_players):
            player_idx = (base_offset + i) % num_players
            player_viable = viable_decisions[player_idx]
            if player_viable and decision in player_viable:
                player_decision = player_decisions[player_idx]
                if player_decision not in player_viable:
                    # player i hasn't make a decision,
                    # this returned value indicates we need to wait for him
                    return [(player_idx, None)]
                elif player_decision == decision:
                    # player i made a decision
                    return [(player_idx, decision)]

    # everybody skips or nobody can do anything
    return None


def score(context, match_results):
    return scoring.score(context.settings.scorer, match_results,
                         context.settings.patterns_score)


def can_4_kong_win(context, player_idx, tile):
    '''
    'Four-kongs' is a special scenario because we need to display 'win'
    instead of 'kong' as an option for the player. So in the game logic, use
    this function to determine if should list 'kong' in the viable decisions.

    '''
    if 'four-kongs' in context.settings.patterns_win:
        if patterns.match('four-kongs', context, player_idx, tile):
            return True
    return False


def get_decision(context, player_idx=None, viable_decisions=None):
    '''
    Get the player's decision. This decision can come from the human player
    (Player.decision) or a bot. Return None if the player hasn't made the
    decision or made an invalid decision.

    '''
    if player_idx is None:
        player_idx = context.cur_player_idx
    player = context.players[player_idx]
    viable_decisions = viable_decisions or player.extra.get('viable_decisions')
    if viable_decisions:
        if player.extra.get('bot'):
            return bots.get().make_decision(context, player_idx, viable_decisions)
        if player.extra.get('declared_ready'):
            if context.state == 'discarding':
                return player.hand.last_tile
            else:
                if 'win' in viable_decisions:
                    return 'win'
                return 'skip'
        if player.decision in viable_decisions:
            return player.decision
    return None


def _get_player_index(context, player_idx=None):
    if player_idx is None:
        player_idx = context.cur_player_idx
        if player_idx is None:
            raise ValueError('Must specify player_idx')
    return player_idx


def _get_incoming_tile(context, player_idx, tile=None):
    '''
    Try to find the incoming tile with the following order:
    1. Parameter ``tile``
    2. ``Hand.last_tile``
    3. ``context.last_discarded()``

    '''
    player = context.players[player_idx]
    hand = player.hand
    if not tile:
        tile = hand.last_tile or context.last_discarded()
        if not tile:
            raise ValueError('Needs an incoming tile')
    return tile


def _copy_scores(scores):
    result = {}
    for name, match_result in scores.iteritems():
        result[name] = match_result.clone()
    return result


def _filter_scores(scores, attr_name, subtract_func):
    result = _copy_scores(scores)

    for name, match_result in scores.iteritems():
        pattern = patterns.get(name)
        other_names = getattr(pattern, attr_name)
        if other_names:
            for other_name in other_names:
                match_result2 = result.get(other_name)
                if match_result2:
                    subtract_func(pattern, match_result, other_name, match_result2)
                    if not match_result2:
                        result.pop(other_name, None)

    return result
