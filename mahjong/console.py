'''
Mahjong game in console mode.

Call ``console.run()`` to start the game.

'''
from mahjong import flow
from mahjong.types import GameContext, Tile, Wall


def run(seed=1):
    context = GameContext()
    context.wall = Wall()

    while True:
        if context.state == 'start':
            context.players[0].extra['bot'] = True
            context.players[1].extra['bot'] = True
            context.players[2].extra['bot'] = True

        result = flow.next(context)
        if result:
            _print_context(context)
        elif result.reason == 'decisions-needed':
            if result.viable_decisions and context.state != 'discarding':
                print 'Viable decisions: %s' % result.viable_decisions[3]
            for i in xrange(0, 4):
                print 'P%d: %s' % (i, context.players[i].hand)
            decision = raw_input('Decision: ')
            if decision == 'exit':
                break
            else:
                if context.state == 'discarding':
                    decision = getattr(Tile, decision.upper())
                elif context.state == 'chowing':
                    tile_names = decision.split(' ')
                    decision = tuple([getattr(Tile, name.upper()) for name in tile_names])
                context.players[3].decision = decision
        else:
            print context.state
            raise Exception(result.reason)


def _print_context(context):
    name = context.state.replace('-', '_')
    func = globals()['_print_' + name]
    func(context)


def _print_start(context):
    print '----------------------------------------------------'
    print 'Start'
    print '  => Round: %d' % context.round
    print '     Match: %d' % context.match
    print '     Dealer: P%s (%d defended)' % (context.dealer, context.dealer_defended)


def _print_wall_built(context):
    print 'Wall built'


def _print_dealt(context):
    print 'Dealt'


def _print_drawing(context):
    print '----------------------------------------------------'


def _print_drawn(context):
    print 'P%d has drawn a %s' % (context.cur_player_idx, context.player().hand.last_tile)
    print '  => %s left in the wall' % context.wall.num_tiles()


def _print_discarding(context):
    print 'P%d is discarding...' % context.cur_player_idx


def _print_discarded(context):
    print 'P%d discarded a %s' % (context.cur_player_idx, context.last_discarded())
    print '  => Discarded pool: %s' % context.discarded_pool


def _print_melding(context):
    print 'Melding time! Last discarded: %s' % (context.last_discarded())


def _print_chowing(context):
    print 'chowing...'


def _print_self_konging(context):
    print 'self konging...'


def _print_end(context):
    if context.winners:
        print 'End, winners:'
        for i in context.winners:
            winner = context.players[i]
            print '  => P%d (%s)' % (i, winner.extra.get('win_type'))
    else:
        print 'End: tie (%s)' % context.extra.get('tie_type')


def _print_scored(context):
    print 'Scored'
    if context.winners:
        for i in context.winners:
            winner = context.players[i]
            scoring_table = winner.extra.get('scoring')
            print 'P%d' % i
            for pattern_name, match_result in scoring_table.iteritems():
                print '  %s: %s' % (pattern_name, match_result)
