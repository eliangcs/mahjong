'''
The flow module has only one public function: ``flow.next()``. You should
**NOT** have to use other classes or functions in this module because those
are meant to be private.

``flow.next()`` is the implementation of the game logic. It transits a
GameContext from a state to another.

'''
from mahjong import algo, patterns
from mahjong.types import Tile, TileGroup


def next(context):
    handler = _STATE_ROUTES.get(context.state)
    if not handler:
        raise ValueError('Illegal game state: `%s`' % context.state)
    return handler.handle(context)


class FlowResult(object):
    '''
    An object type returned by flow.next().

    This object tells you if the transition is successful. If not, it will
    have a string assigned to FlowResult.reason indicating the reason why it
    failed. FlowResult.reason could be one of these values:
    * 'bad-context': The game context contains some invalid values. Normally
      this shouldn't happen if you manipulate the game context properly.
    * 'decisions-needed': One or more players must make decisions before the
      game can go on.

    FlowResult.viable_decisions is available when the reason is
    'decisions-needed'. It's a list of four sub-lists, and each sub-list
    contains the decisions which the ith player can make.

    '''
    def __init__(self, success, reason=None, viable_decisions=None):
        self.success = success
        self.reason = reason
        self.viable_decisions = viable_decisions

    def __nonzero__(self):
        return self.success

    def set_viable_decisions(self, player_idx, viable_decisions):
        if not self.viable_decisions:
            self.viable_decisions = [None, None, None, None]
        self.viable_decisions[player_idx] = viable_decisions


class Handler(object):
    '''
    Abstract superclass for all the handlers in this module.

    '''
    def handle(self, context):
        result = self.validate(context)
        if not result:
            return result
        self.next(context)
        return result

    def validate(self, context):
        '''
        Return a FlowResult indicating if a GameContext can be taken to the
        next state.

        Override this method if necessary. The input GameContext should remain
        intact if this method returns a failed FlowResult.

        '''
        return FlowResult(True)

    def next(self, context):
        '''
        Take a GameContext to the next state.

        Subclasses should always implement this method.

        '''
        raise NotImplementedError


class StartHandler(Handler):
    '''
    Handler for 'start' state.

    Incoming state: 'scored'.
    Outgoing state: 'wall-built'.

    StartHandler takes a game context from 'start' to 'wall-built'. All it
    does is reset and shuffle the wall.

    '''
    def validate(self, context):
        if not context.wall:
            return FlowResult(False, 'bad-context')
        return FlowResult(True)

    def next(self, context):
        # build wall
        context.wall.reset()
        context.wall.shuffle()
        context.state = 'wall-built'


class WallBuiltHandler(Handler):
    '''
    Handler for 'wall-built' state.

    Incoming state: 'start'.
    Outgoing state: 'dealt'.

    Once the wall is built, WallBuiltHandler deals the tiles to each player.

    '''
    def validate(self, context):
        if context.wall.num_tiles() == context.settings.total_tiles():
            return FlowResult(True)
        return FlowResult(False, 'bad-context')

    def next(self, context):
        # number of tiles per hand
        num_hand_tiles = context.settings.num_hand_tiles

        # deal to players
        for player in context.players:
            hand = player.hand
            for __ in xrange(num_hand_tiles):
                tile = context.wall.draw()
                hand.add_free_tile(tile)

        context.state = 'dealt'


class DealtHandler(Handler):
    '''
    Handler for 'dealt' state.

    Incoming state: 'wall-built'.
    Outgoing state: 'drawing'.

    If any of the players has flowers, DealtHandler replaces those flowers by
    drawing more tiles from the wall.

    '''
    def validate(self, context):
        num_tiles_left = context.settings.total_tiles() - context.settings.num_hand_tiles * 4
        if context.wall.num_tiles() == num_tiles_left:
            return FlowResult(True)
        return FlowResult(False, 'bad-context')

    def next(self, context):
        # draw more tiles until all flowers are replaced
        if context.settings.wall_flowers:
            num_hand_tiles = context.settings.num_hand_tiles
            counter = 1
            while counter:
                counter = 0
                for player in context.players:
                    hand = player.hand
                    hand.move_flowers()
                    # draw until each has num_hand_tiles tiles
                    while len(hand.free_tiles) < num_hand_tiles:
                        tile = context.wall.draw()
                        hand.add_free_tile(tile)
                        counter += 1

        context.state = 'drawing'


class DrawingHandler(Handler):
    '''
    Handler for 'drawing' state.

    Incoming state: 'dealt'.
    Outgoing states:
    1. 'end' if wall tie (not enough tiles left in the wall).
    2. 'drawn' otherwise.

    '''
    def validate(self, context):
        player = context.player()
        hand = player.hand
        if hand.last_tile:
            return FlowResult(False, 'bad-context')

        # if the player just drew a flower
        if player.extra.get('flowered'):
            if not hand.flowers:
                return FlowResult(False, 'bad-context')

            # if there's someone who can win with the flower,
            # wait until he makes the decision
            robber_idx, chucker_idx = self._player_who_can_flower_win(context)
            if robber_idx is not None and chucker_idx is not None:
                viable_decisions = ['win', 'skip']
                robber = context.players[robber_idx]

                # if player declared ready or turned on bot mode,
                # then player's decision doesn't matter
                if not algo.get_decision(context, robber_idx, viable_decisions):
                    result = FlowResult(False, 'decisions-needed')
                    result.set_viable_decisions(robber_idx, viable_decisions)
                    return result

                # save these in context for later use in next()
                context.extra.update({
                    'flower_winner': robber_idx,
                    'flower_chucker': chucker_idx
                })
                robber.extra['viable_decisions'] = viable_decisions

        return FlowResult(True)

    def next(self, context):
        # wall doesn't have enough tiles left -> tie
        if context.is_tie(four_waiting=False, four_kongs=False, four_winds=False):
            context.winners = None
            context.state = 'end'
            context.extra['tie_type'] = 'wall'
            self._cleanup(context)
            return

        # if someone wants to rob the flower
        robber_idx, chucker_idx = self._player_who_wants_to_flower_win(context)
        if robber_idx is not None and chucker_idx is not None:
            robber = context.players[robber_idx]
            chucker = context.players[chucker_idx]

            # give chucker's flower to robber
            flower = chucker.hand.flowers.pop()
            robber.hand.add_flower(flower)
            robber.extra['flowered'] = True
            chucker.extra.pop('flowered', None)

            # robber's turn to draw another tile
            if context.cur_player_idx != robber_idx:
                context.set_turn(robber_idx)

        # draw a tile from the wall
        context.player().hand.last_tile = context.wall.draw()
        context.state = 'drawn'

        self._cleanup(context)

    def _player_who_can_flower_win(self, context):
        '''Return a tuple of (robber index, index of player who got robbed).'''
        if 'seven-flowers' in context.settings.patterns_win:
            # check if someone ELSE can rob this player's flower
            player = context.player()
            num_flowers = len(player.hand.flowers)
            if num_flowers == 1:
                for i in xrange(1, 4):
                    player_idx = (context.cur_player_idx + i) % 4
                    if len(context.players[player_idx].hand.flowers) == 7:
                        return player_idx, context.cur_player_idx

            # check if THIS player can rob someone else's flower
            if num_flowers == 7:
                for i in xrange(1, 4):
                    player_idx = (context.cur_player_idx + i) % 4
                    if context.players[player_idx].hand.flowers:
                        return context.cur_player_idx, player_idx

        return None, None

    def _player_who_wants_to_flower_win(self, context):
        player = context.player()
        if player.extra.get('flowered'):
            robber_idx = context.extra.get('flower_winner')
            chucker_idx = context.extra.get('flower_chucker')
            if robber_idx is not None and chucker_idx is not None:
                # decision can be made by automatic bot or player
                decision = algo.get_decision(context, robber_idx)

                if decision == 'win':
                    return robber_idx, chucker_idx

        return None, None

    def _cleanup(self, context):
        #for player in context.players:
        #    player.extra.pop('flowered', None)
        flower_winner_idx = context.extra.pop('flower_winner', None)
        if flower_winner_idx is not None:
            flower_winner = context.players[flower_winner_idx]
            flower_winner.extra.pop('viable_decisions', None)


class DrawnHandler(Handler):
    '''
    Handler for 'drawn' state.

    Incoming state: 'drawing'.
    Outgoing states:
    1. 'drawing' if the player just drew a flower.
    2. 'end' if self-picking or flower winning.
    3. 'self-konging': if the player made a self-kong.
    4. 'discarding' otherwise.

    '''
    def validate(self, context):
        player = context.player()
        hand = player.hand
        if not (hand and hand.last_tile):
            return FlowResult(False, 'bad-context')

        if hand.last_tile.is_general_flower():
            return FlowResult(True)

        # viable_decisions can be one of these:
        # []
        # ['win', 'skip']
        # ['kong', 'skip']
        # ['win', 'kong', 'skip']
        viable_decisions = self._get_viable_decisions(context)

        # player has no choices
        if not viable_decisions:
            return FlowResult(True)

        # check if player has made a valid decision
        decision = algo.get_decision(context, viable_decisions=viable_decisions)
        if not decision:
            result = FlowResult(False, 'decisions-needed')
            result.set_viable_decisions(context.cur_player_idx, viable_decisions)
            return result

        # can win but doesn't want to win -> water penalty
        if context.settings.water and decision != 'win' and 'win' in viable_decisions:
            player.extra['water'] = algo.waiting_tiles(context)

        # player decision is valid
        player.extra['viable_decisions'] = viable_decisions
        return FlowResult(True)

    def next(self, context):
        player = context.player()
        hand = player.hand
        if hand.last_tile.is_general_flower():
            # if player drew a flower, go back to 'drawing'
            hand.move_flowers()
            context.state = 'drawing'

            # for DrawingHandler to check for seven-flowers
            player.extra['flowered'] = True
            self._cleanup(context)
            return

        decision = algo.get_decision(context)
        if decision:
            if decision == 'win' and self._is_appended_kong(context):
                # 4-kong win
                self._kong(context)
                self._cleanup(context)
                return

            routes = {
                'win': self._win,
                'kong': self._kong,
                'skip': self._skip
            }
            method = routes.get(decision)
            method(context)
        else:
            # player has no choice but skip
            self._skip(context)

        self._cleanup(context)

    def _is_appended_kong(self, context):
        player = context.player()
        hand = player.hand
        tile = hand.last_tile
        if hand.num_kongs() == 3:
            for group in hand.fixed_groups:
                if group.group_type == TileGroup.PONG and group.tiles[0] == tile:
                    return True
        return False

    def _get_viable_decisions(self, context):
        player = context.player()
        hand = player.hand
        viable_decisions = []
        if algo.can_win(context, context.cur_player_idx):
            viable_decisions.append('win')
        if hand.can_self_kong() and not algo.can_4_kong_win(context, context.cur_player_idx, hand.last_tile):
            viable_decisions.append('kong')
        if viable_decisions:
            # 'skip' is available only if 'win' or 'kong' is available
            viable_decisions.append('skip')
        return viable_decisions

    def _skip(self, context):
        context.state = 'discarding'

    def _win(self, context):
        player = context.player()

        context2 = context.clone()
        del context2.player().hand.flowers[:]

        can_win_without_flowers = algo.can_win(context2)
        if can_win_without_flowers:
            # flower win + self-pick in the hand
            player.extra['win_type'] = 'self-picked'
        else:
            # flower win but the hand itself cannot win
            player.extra['win_type'] = 'flower-won'

        context.winners = [context.cur_player_idx]
        context.state = 'end'

    def _kong(self, context):
        # check if the player can remove his water penalty
        if context.settings.water:
            player = context.player()
            tile_to_kong = player.hand.last_tile
            waiting_tiles = player.extra.get('water')
            if waiting_tiles and tile_to_kong not in waiting_tiles:
                del player.extra['water']

        context.state = 'self-konging'

    def _cleanup(self, context):
        player = context.player()
        if player.decision != 'win':
            player.extra.pop('konged', None)
        if context.state not in ('drawing', 'end'):
            player.extra.pop('flowered', None)
        player.decision = None
        player.extra.pop('viable_decisions', None)


class SelfKongingHandler(Handler):
    '''
    Handler for 'self-konging' state.

    Incoming state: 'drawn'.
    Outgoing states:
    1. 'end' if someone robs the kong or 4-kong win/tie.
    2. 'drawing' otherwise.

    '''
    def validate(self, context):
        player = context.player()
        hand = player.hand
        if not hand.last_tile:
            return FlowResult(False, 'bad-context')

        kong_type = None
        if hand.can_concealed_kong():
            kong_type = 'concealed'
        elif hand.can_appended_kong():
            kong_type = 'appended'

        if not kong_type:
            return FlowResult(False, 'bad-context')

        # check if anyone can rob the kong
        if kong_type == 'appended':
            viable_decisions = self._get_viable_decisions(context)
            player_decisions = self._get_player_decisions(context, viable_decisions)
            winners = algo.select_melders(viable_decisions, player_decisions)

            if winners:
                invalid_decision = not winners[0][1]
                if invalid_decision:
                    # block until player gives a valid decision
                    return FlowResult(False, 'decisions-needed', viable_decisions)
                context.extra['winners'] = [x[0] for x in winners]

            # check if anyone can win but doesn't want to win -> water penalty
            if context.settings.water:
                for i in xrange(0, 4):
                    viable = viable_decisions[i]
                    decision = player_decisions[i]
                    if viable and 'win' in viable and decision != 'win':
                        context.players[i].extra['water'] = algo.waiting_tiles(context, i)

        return FlowResult(True)

    def next(self, context):
        winners = context.extra.get('winners')
        if winners:
            self._rob_kong(context, winners)
        else:
            self._kong(context)

        self._cleanup(context)

    def _rob_kong(self, context, winners):
        hand = context.player().hand
        context.discard(hand.last_tile)
        if context.settings.multi_winners:
            context.winners = winners
        else:
            context.winners = winners[:1]
        context.state = 'end'

        for winner_idx in context.winners:
            winner = context.players[winner_idx]
            winner.extra['win_type'] = 'robbed'
            winner.extra['chucker'] = context.cur_player_idx

    def _kong(self, context):
        player = context.player()
        hand = player.hand
        tile_to_kong = hand.last_tile
        hand.kong_from_self()

        if algo.can_win(context, incoming_tile=tile_to_kong):
            # 4-kong win
            context.state = 'end'
            context.winners = [context.cur_player_idx]
            player.extra['win_type'] = 'self-picked'
        elif context.is_tie(four_waiting=False, wall_tie=False, four_winds=False):
            context.state = 'end'
            context.winners = None
            context.extra['tie_type'] = '4-kong'
        else:
            context.state = 'drawing'

            # to identify 'konged-or-flowered' pattern
            player.extra['konged'] = True

    def _get_viable_decisions(self, context):
        decisions = [None, None, None, None]
        tile_to_kong = context.player().hand.last_tile
        for i in xrange(1, 4):
            player_idx = (context.cur_player_idx + i) % 4
            player = context.players[player_idx]
            if 'viable_decisions' in player.extra:
                decisions[player_idx] = player.extra.get('viable_decisions')
            elif algo.can_win(context, player_idx, tile_to_kong):
                viable = ['win', 'skip']
                decisions[player_idx] = viable
                player.extra['viable_decisions'] = viable
            else:
                player.extra['viable_decisions'] = None
        return decisions

    def _get_player_decisions(self, context, viable_decisions):
        result = []
        for i in xrange(0, 4):
            decision = algo.get_decision(context, i, viable_decisions[i])
            result.append(decision)
        return result

    def _cleanup(self, context):
        context.extra.pop('winners', None)
        for player in context.players:
            player.extra.pop('viable_decisions', None)
            player.decision = None


class DiscardingHandler(Handler):
    '''
    Handler for 'discarding' state.

    Incoming states: 'drawn', 'melding', 'chowing'.
    Outgoing state: 'discarded'.

    DiscardingHandler waits for the player to discard a tile in his hand.

    '''
    def validate(self, context):
        player = context.player()
        hand = player.hand

        # decision should be a tile to be discarded
        viable_decisions = set(hand.free_tiles + [hand.last_tile])
        decision = algo.get_decision(context, viable_decisions=viable_decisions)
        if not (isinstance(decision, Tile) and hand.contains(decision)):
            result = FlowResult(False, 'decisions-needed')
            result.set_viable_decisions(context.cur_player_idx, viable_decisions)
            return result

        player.decision = decision
        return FlowResult(True)

    def next(self, context):
        player = context.player()
        tile = player.decision
        context.discard(tile)
        context.state = 'discarded'

        # check if it can remove water penalty
        if context.settings.water:
            waiting_tiles = player.extra.get('water')
            if waiting_tiles and tile not in waiting_tiles:
                del player.extra['water']

        self._cleanup(context)

    def _cleanup(self, context):
        context.player().decision = None


class DiscardedHandler(Handler):
    '''
    Handler for 'discarded' state.

    Incoming states: 'discarding', 'discarded'.
    Outgoing states:
    1. 'end' if 4-wind tie or 4-waiting tie.
    2. 'discarded' if player decalre ready.
    3. 'melding' if someone can meld the discarded tile.
    4. 'drawing' if no one can meld the discarded tile.

    '''
    def validate(self, context):
        player = context.player()
        if player is None or not context.last_discarded():
            return FlowResult(False, 'bad-context')

        # 4-wind or 4-waiting tie
        if context.is_tie(four_kongs=False, wall_tie=False):
            context.extra['tie'] = True
            return FlowResult(True)

        # if player has a ready hand, ask player if he wants to declare
        # player.extra['asked'] is a flag indicating 'declare/skip' options have been asked,
        # and player won't be asked again if he answers 'skip'
        if context.settings.declarable and not player.extra.get('asked') and algo.ready(context):
            player.extra['ready'] = True
            viable_decisions = ['declare', 'skip']
            decision = algo.get_decision(context, viable_decisions=viable_decisions)
            if not decision:
                result = FlowResult(False, 'decisions-needed')
                result.set_viable_decisions(context.cur_player_idx, viable_decisions)
                return result

            player.decision = decision

        return FlowResult(True)

    def next(self, context):
        player = context.player()
        if context.extra.get('tie'):
            # 4-wind or 4-waiting tie
            self._tie(context)
            self._cleanup(context)
            return

        if player.extra.get('ready') and not player.extra.get('asked'):
            # assert player.decision in ('declare', 'skip')
            if player.decision == 'declare':
                self._declare_ready(context)
            self._cleanup(context)
            player.extra['asked'] = True
            return

        viable_decisions = self._get_viable_decisions(context)
        someone_can_meld = len(filter(lambda x: bool(x), viable_decisions)) > 0
        if someone_can_meld:
            context.state = 'melding'
            for i in xrange(0, 4):
                if viable_decisions[i]:
                    context.players[i].extra['viable_decisions'] = viable_decisions[i]
        else:
            # nobody can do anything with the discarded tile
            context.state = 'drawing'
            context.next_turn()

        self._cleanup(context)

    def _tie(self, context):
        context.state = 'end'
        context.winners = None
        ready_players = filter(lambda p: p.extra.get('declared_ready'), context.players)
        if len(ready_players) < 4:
            context.extra['tie_type'] = '4-wind'
        else:
            context.extra['tie_type'] = '4-waiting'

    def _declare_ready(self, context):
        player = context.player()
        player.extra.update({
            'declared_ready': True,
            'waiting_tiles': algo.waiting_tiles(context)
        })

        # for heaven-ready or earth-ready patterns
        if len(player.discarded) == 1:
            player.extra['immediate_ready'] = True

    def _cleanup(self, context):
        player = context.player()
        player.extra.pop('ready', None)
        player.extra.pop('asked', None)
        context.extra.pop('tie', None)
        for player in context.players:
            player.decision = None

    def _get_viable_decisions(self, context):
        '''Get viable decisions for four players.'''
        decisions = [None, None, None, None]
        for i in xrange(1, 4):
            player_idx = (context.cur_player_idx + i) % 4
            decisions[player_idx] = self._get_other_viable_decisions(context, player_idx)
        return decisions

    def _get_other_viable_decisions(self, context, player_idx):
        '''Get viable decisions for players except for the current one.'''
        decisions = []
        player = context.players[player_idx]
        hand = player.hand
        tile = context.last_discarded()

        if algo.can_win(context, player_idx=player_idx, incoming_tile=tile):
            decisions.append('win')

        # if player declared ready, he can't kong, pong, chow
        if not player.extra.get('declared_ready'):
            if hand.can_kong(tile) and not algo.can_4_kong_win(context, player_idx, tile):
                # if player can 4-kong win, display 'win' option instead of 'kong'
                decisions.append('kong')
            if hand.can_pong(tile):
                decisions.append('pong')
            if (context.cur_player_idx + 1) % 4 == player_idx and hand.can_chow(tile):
                decisions.append('chow')

        if decisions:
            decisions.append('skip')
        return decisions


class MeldingHandler(Handler):
    '''
    Handler for 'melding' state.

    Incoming state: 'discarded'.
    Outgoing states:
    1. 'end' if someone wants to win or 4-kong tie.
    2. 'drawing' if no one wants to meld.
    3. 'chowing' if chow is selected and there're multiple ways to chow.
    4. 'discarding' if someone wants to kong, pong, or chow.

    MeldingHandler assumes that the viable decisions for each player is stored
    in ``context.players[i].extra['viable_decisions']``.

    '''
    def validate(self, context):
        player = context.player()
        if not (player and context.last_discarded()):
            return FlowResult(False, 'bad-context')

        # check if last discarded tile is valid
        if context.last_discarded() != player.discarded[-1]:
            return FlowResult(False, 'bad-context')

        # check if there's a least one player have choices
        # if there're no choices for players, the context shouldn't go into this state in the first place
        viable_decisions = [p.extra.get('viable_decisions') for p in context.players]
        no_one_can_meld = len(filter(lambda x: bool(x), viable_decisions)) == 0
        if no_one_can_meld:
            return FlowResult(False, 'bad-context')

        # check if players' decisions are valid
        player_decisions = self._get_player_decisions(context)
        melders = algo.select_melders(viable_decisions, player_decisions)
        if melders:
            invalid_decision = not melders[0][1]
            if invalid_decision:
                # block until player gives a valid decision
                return FlowResult(False, 'decisions-needed', viable_decisions)
            context.extra['melders'] = melders

        # check if anyone can win and doesn't want to win -> water penalty
        if context.settings.water:
            for i in xrange(0, 4):
                viable = viable_decisions[i]
                decision = player_decisions[i]
                if decision != 'win' and viable and 'win' in viable:
                    context.players[i].extra['water'] = algo.waiting_tiles(context, i)

        return FlowResult(True)

    def next(self, context):
        melders = context.extra.get('melders')

        # no one wants to meld -> next player to draw
        if not melders:
            self._next_turn(context)
            self._cleanup(context)
            return

        # someone won
        first_decision = melders[0][1]
        if first_decision == 'win':
            winners = [x[0] for x in melders]
            self._win(context, winners)
            self._cleanup(context)
            return

        # chow: chould have multiple way to chow
        if first_decision == 'chow':
            tile_to_chow = context.last_discarded()
            chower_idx = melders[0][0]
            chower = context.players[chower_idx]
            chow_combs = chower.hand.get_chow_combs(tile_to_chow)
            if len(chow_combs) > 1:
                self._multi_chow(context, chower_idx, chow_combs)
            else:
                # assert len(chow_combs) == 1
                self._single_chow(context, chower_idx, chow_combs[0])
            self._cleanup(context)
            return

        # kong or pong
        melder_idx = melders[0][0]
        routes = {
            'kong': self._kong,
            'pong': self._pong
        }
        method = routes.get(first_decision)
        method(context, melder_idx)
        self._cleanup(context)

    def _get_player_decisions(self, context):
        result = []
        for i in xrange(0, 4):
            decision = algo.get_decision(context, i)
            result.append(decision)
        return result

    def _next_turn(self, context):
        context.state = 'drawing'
        context.next_turn()

    def _win(self, context, winners):
        context.state = 'end'
        if context.settings.multi_winners:
            context.winners = winners
        else:
            context.winners = winners[:1]

        for winner_idx in context.winners:
            winner = context.players[winner_idx]
            winner.extra['win_type'] = 'melded'
            winner.extra['chucker'] = context.cur_player_idx

    def _tie(self, context):
        context.state = 'end'
        context.extra['tie_type'] = '4-kong'
        context.winners = None

    def _kong(self, context, melder_idx):
        tile = context.remove_last_discarded()
        context.state = 'drawing'
        context.set_turn(melder_idx)
        player = context.player()
        player.hand.kong_from_other(tile)

        # to identify 'konged-or-flowered' pattern
        player.extra['konged'] = True

        # 4-kong tie
        if context.is_tie(four_waiting=False, wall_tie=False, four_winds=False):
            self._tie(context)

    def _pong(self, context, melder_idx):
        tile = context.remove_last_discarded()
        context.state = 'discarding'
        context.set_turn(melder_idx)
        context.player().hand.pong(tile)

    def _multi_chow(self, context, chower_idx, chow_combs):
        chower = context.players[chower_idx]
        chower.extra['chow_combs'] = chow_combs
        context.state = 'chowing'
        context.set_turn(chower_idx)

    def _single_chow(self, context, chower_idx, chow_comb):
        tile = context.remove_last_discarded()
        context.state = 'discarding'
        context.set_turn(chower_idx)
        context.player().hand.chow(chow_comb, tile)

    def _cleanup(self, context):
        context.extra.pop('melders', None)
        for player in context.players:
            player.extra.pop('viable_decisions', None)
            player.decision = None
        if context.state != 'win':
            context.player().extra.pop('konged', None)


class ChowingHandler(Handler):
    '''
    Handler for 'chowing' state.

    Incoming state: 'melding'.
    Outgoing state: 'discarding'.

    ChowingHandler assumes the viable chow combinations are stored in
    ``context.players[i].extra['chow_combs']``.

    '''
    def validate(self, context):
        if not context.last_discarded():
            return FlowResult(False, 'bad-context')

        cur_player = context.player()
        if not (cur_player and cur_player.extra.get('chow_combs')):
            return FlowResult(False, 'bad-context')

        last_player = context.player(-1)
        if not (last_player and context.last_discarded() == last_player.discarded[-1]):
            return FlowResult(False, 'bad-context')

        chow_combs = cur_player.extra.get('chow_combs')
        if cur_player.decision not in chow_combs:
            result = FlowResult(False, 'decisions-needed')
            result.set_viable_decisions(context.cur_player_idx, chow_combs)
            return result

        return FlowResult(True)

    def next(self, context):
        player = context.player()
        chow_comb = player.decision
        tile = context.remove_last_discarded(-1)
        player.hand.chow(chow_comb, tile)
        context.state = 'discarding'
        self._cleanup(context)

    def _cleanup(self, context):
        player = context.player()
        player.decision = None
        player.extra.pop('chow_combs', None)


class EndHandler(Handler):
    '''
    Handler for 'end' state.

    Incoming states: 'discarded', 'drawing', 'drawn', 'melding',
                     'self-konging'.
    Outgoing states: 'scored'.

    # TODO: bloodmatch

    '''
    def validate(self, context):
        # it's either win or tie
        if context.winners:
            for i in context.winners:
                winner = context.players[i]
                if not winner.extra.get('win_type'):
                    return FlowResult(False, 'bad-context')
        elif not context.extra.get('tie_type'):
            return FlowResult(False, 'bad-context')

        return FlowResult(True)

    def next(self, context):
        if context.winners:
            for winner_idx in context.winners:
                winner = context.players[winner_idx]
                winner.extra['patterns_matched'] = patterns.match_all(context, winner_idx)
        context.state = 'scored'


class ScoredHandler(Handler):
    '''
    Handler for 'scored' handler.

    Incoming state: 'end'.
    Outgoing state: 'start'.

    ScoredHandler clears all intermediate data in the game context (mostly in
    ``context.extra`` and ``context.players[i].extra``), decides the next
    dealer, and initializes for the next match.

    '''
    def next(self, context):
        self._clear_hands(context)
        self._update_round_and_match(context)
        self._set_next_dealer(context)

        # reset rest of fields
        context.winners = None
        context.state = 'start'
        context.extra.clear()

    def _clear_hands(self, context):
        context.reset_players()
        del context.discarded_pool[:]
        context.cur_player_idx = 0
        context.last_player_idx = None

    def _update_round_and_match(self, context):
        if self._should_goto_next_round(context):
            context.round += 1
            context.match = 0
        else:
            context.match += 1

    def _set_next_dealer(self, context):
        next_dealer = self._get_next_dealer(context)
        if next_dealer == context.dealer:
            context.dealer_defended += 1
        else:
            context.dealer = next_dealer
            context.dealer_defended = 0

    def _should_goto_next_round(self, context):
        next_dealer = self._get_next_dealer(context)
        return context.dealer == 3 and next_dealer != context.dealer

    def _get_next_dealer(self, context):
        # tie or dealer wins -> dealer defends
        if ((not context.winners or context.dealer in context.winners) and
                context.dealer_defended < context.settings.max_dealer_defended):
            return context.dealer
        return (context.dealer + 1) % 4


# Routing table that maps a game state to a handler
_STATE_ROUTES = {
    'start': StartHandler(),
    'wall-built': WallBuiltHandler(),
    'dealt': DealtHandler(),
    'drawing': DrawingHandler(),
    'drawn': DrawnHandler(),
    'self-konging': SelfKongingHandler(),
    'discarding': DiscardingHandler(),
    'discarded': DiscardedHandler(),
    'melding': MeldingHandler(),
    'chowing': ChowingHandler(),
    'end': EndHandler(),
    'scored': ScoredHandler()
}
