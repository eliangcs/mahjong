def get(name='dumb'):
    return _BOTS.get(name)


class DumbBot(object):

    def make_decision(self, context, player_idx=None, viable_decisions=None):
        if player_idx is None:
            player = context.player()
        else:
            player = context.players[player_idx]
        if context.state == 'discarding':
            return player.hand.last_tile

        viable_decisions = viable_decisions or player.extra.get('viable_decisions', [])
        if 'win' in viable_decisions:
            return 'win'
        if 'skip' in viable_decisions:
            return 'skip'
        return None


_BOTS = {
    'dumb': DumbBot()
}
