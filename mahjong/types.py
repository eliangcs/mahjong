import bisect
import copy
import random

from collections import Counter

from mahjong import utils


class Tile(object):
    '''
    A mahjong tile.

    All necessary tile instances are created when this module is loaded, so do
    **NOT** call the constructor at runtime. Do this instead::

        t1 = Tile.CHAR1   # tile instance of 1-character
        t2 = Tile.SUMMER  # tile instance of summer

        t1 == t2          # compare two tiles

        t1.rank == 1      # get tile rank and suit
        t2.suit == Tile.SUIT_FLOWER

    '''
    # Characters
    #------------
    ID_CHAR1 = 0x0101
    ID_CHAR2 = 0x0102
    ID_CHAR3 = 0x0103
    ID_CHAR4 = 0x0104
    ID_CHAR5 = 0x0105
    ID_CHAR6 = 0x0106
    ID_CHAR7 = 0x0107
    ID_CHAR8 = 0x0108
    ID_CHAR9 = 0x0109

    # Circles
    #---------
    ID_CIRCLE1 = 0x0201
    ID_CIRCLE2 = 0x0202
    ID_CIRCLE3 = 0x0203
    ID_CIRCLE4 = 0x0204
    ID_CIRCLE5 = 0x0205
    ID_CIRCLE6 = 0x0206
    ID_CIRCLE7 = 0x0207
    ID_CIRCLE8 = 0x0208
    ID_CIRCLE9 = 0x0209

    # Bamboos
    #---------
    ID_BAMBOO1 = 0x0401
    ID_BAMBOO2 = 0x0402
    ID_BAMBOO3 = 0x0403
    ID_BAMBOO4 = 0x0404
    ID_BAMBOO5 = 0x0405
    ID_BAMBOO6 = 0x0406
    ID_BAMBOO7 = 0x0407
    ID_BAMBOO8 = 0x0408
    ID_BAMBOO9 = 0x0409

    # Honors
    #--------
    # Winds
    ID_EAST = 0x1000
    ID_SOUTH = 0x1002
    ID_WEST = 0x1004
    ID_NORTH = 0x1006
    # Dragons
    ID_RED = 0x1800
    ID_GREEN = 0x1802
    ID_WHITE = 0x1804

    # Flowers
    #---------
    # Flowers
    ID_PLUM = 0x4000
    ID_ORCHID = 0x4002
    ID_BAMBOO = 0x4004
    ID_CHRYSANTH = 0x4006
    # Seaons
    ID_SPRING = 0x6000
    ID_SUMMER = 0x6002
    ID_AUTUMN = 0x6004
    ID_WINTER = 0x6006

    # Suit enumerations
    SUIT_CHAR = 0x0100
    SUIT_CIRCLE = 0x0200
    SUIT_BAMBOO = 0x0400
    SUIT_WIND = 0x1000
    SUIT_DRAGON = 0x1800
    SUIT_FLOWER = 0x4000
    SUIT_SEASON = 0x6000

    # Masks
    MASK_CHAR = 0x0100
    MASK_CIRCLE = 0x0200
    MASK_BAMBOO = 0x0400
    MASK_HONOR = 0x1000
    MASK_FLOWER = 0x4000
    MASK_DRAGON = 0x0800
    MASK_SEASON = 0x2000

    def __init__(self, tile_id):
        self.tile_id = tile_id
        self.name = Tile._NAMES.get(tile_id)

        # set tile suit
        if Tile.MASK_CHAR & self.tile_id:
            self.suit = Tile.SUIT_CHAR
        elif Tile.MASK_CIRCLE & self.tile_id:
            self.suit = Tile.SUIT_CIRCLE
        elif Tile.MASK_BAMBOO & self.tile_id:
            self.suit = Tile.SUIT_BAMBOO
        elif Tile.MASK_HONOR & self.tile_id:
            if Tile.MASK_DRAGON & self.tile_id:
                self.suit = Tile.SUIT_DRAGON
            else:
                self.suit = Tile.SUIT_WIND
        elif Tile.MASK_FLOWER & self.tile_id:
            if Tile.MASK_SEASON & self.tile_id:
                self.suit = Tile.SUIT_SEASON
            else:
                self.suit = Tile.SUIT_FLOWER
        else:
            raise ValueError('Illegal tile_id: %s' % hex(tile_id))

        # set tile rank (None if not viable)
        self.rank = tile_id % 16 if tile_id < 0x1000 else None

        self.suit_name = Tile._SUIT_NAMES.get(self.suit)

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        if type(other) == type(self):
            return self.tile_id == other.tile_id
        return False

    def __cmp__(self, other):
        return self.tile_id - other.tile_id

    def __hash__(self):
        return self.tile_id

    def is_char(self):
        return self.suit == Tile.SUIT_CHAR

    def is_circle(self):
        return self.suit == Tile.SUIT_CIRCLE

    def is_bamboo(self):
        return self.suit == Tile.SUIT_BAMBOO

    def is_honor(self):
        return self.suit == Tile.SUIT_WIND or self.suit == Tile.SUIT_DRAGON

    def is_wind(self):
        return self.suit == Tile.SUIT_WIND

    def is_dragon(self):
        return self.suit == Tile.SUIT_DRAGON

    def is_general_flower(self):
        return self.suit == Tile.SUIT_FLOWER or self.suit == Tile.SUIT_SEASON

    def is_special_flower(self):
        return self.suit == Tile.SUIT_FLOWER

    def is_season(self):
        return self.suit == Tile.SUIT_SEASON


def _init_tile_class():
    '''
    Dynamically initialize some useful class members in Tile class.

    '''
    Tile._NAMES = {}
    Tile._SUIT_NAMES = {}
    tile_ids = []
    for attr_name in dir(Tile):
        if attr_name.startswith('ID_'):
            # fill Tile._NAMES
            tile_id = getattr(Tile, attr_name)
            tile_name = attr_name[3:]
            Tile._NAMES[tile_id] = tile_name
            tile_ids.append(tile_id)
        elif attr_name.startswith('SUIT_'):
            # fill Tile._SUIT_NAMES
            suit_id = getattr(Tile, attr_name)
            suit_name = attr_name[5:]
            Tile._SUIT_NAMES[suit_id] = suit_name

    # create Tile instances, such as Tile.PLUM
    Tile.ALL = {}
    Tile.CHARS = []
    Tile.CIRCLES = []
    Tile.BAMBOOS = []
    Tile.HONORS = []
    Tile.FLOWERS = []
    Tile.WINDS = []
    Tile.DRAGONS = []
    for tile_id in tile_ids:
        tile_name = Tile._NAMES.get(tile_id)
        tile = Tile(tile_id)
        setattr(Tile, tile_name, tile)
        Tile.ALL[tile_id] = tile

        # add the tile to its suit set
        if tile.is_char():
            suit_set = Tile.CHARS
        elif tile.is_circle():
            suit_set = Tile.CIRCLES
        elif tile.is_bamboo():
            suit_set = Tile.BAMBOOS
        elif tile.is_honor():
            suit_set = Tile.HONORS
        elif tile.is_general_flower():
            suit_set = Tile.FLOWERS
        bisect.insort(suit_set, tile)

        if tile.is_wind():
            bisect.insort(Tile.WINDS, tile)
        elif tile.is_dragon():
            bisect.insort(Tile.DRAGONS, tile)

_init_tile_class()


class TileGroup(object):
    '''
    A TileGroup consists of 3 or 4 tiles. It's a "fixed" (as opposed to
    "free") group in a hand of tiles. "Fixed" means the player can't discard
    it in the game.

    A TileGroup can be one of these types:

    * Chow
    * Pong
    * Exposed kong
    * Concealed kong

    '''
    CHOW = 0
    PONG = 1
    KONG_EXPOSED = 2
    KONG_CONCEALED = 3

    _TYPE_NAMES = ['CHOW', 'PONG', 'KONG_EXPOSED', 'KONG_CONCEALED']

    def __init__(self, tiles, group_type):
        num_tiles = len(tiles)
        if num_tiles != 3 and num_tiles != 4:
            raise ValueError('Argument `tiles` must be a list containing 3 or 4 tiles, you have %d' % num_tiles)

        if group_type < TileGroup.CHOW or group_type > TileGroup.KONG_CONCEALED:
            raise ValueError('Illegal group_type: %d' % group_type)

        self.tiles = sorted(tiles)
        self.group_type = group_type

    def __repr__(self):
        type_name = TileGroup._TYPE_NAMES[self.group_type]
        return '%s%s' % (type_name, self.tiles)

    def __eq__(self, other):
        return self.group_type == other.group_type and self.tiles == other.tiles

    def __hash__(self):
        return sum([hash(tile) for tile in self.tiles])

    def __iter__(self):
        for tile in self.tiles:
            yield tile

    def clone(self):
        tiles = copy.copy(self.tiles)
        return TileGroup(tiles, self.group_type)


class Hand(object):
    '''
    A hand of a player.

    A hand consists of:
    * Free tiles: Tiles that the player can freely discard. Always sorted.
    * Fixed groups: Tiles that have been melded. They can't be removed during
                    a match once they've got created.
    * Flowers: Flower tiles.
    * Last tile: The newly-drawn tile is assigned to this when it just gets
                 drawn. After the player discards a tile, this will be
                 inserted into the free tiles.

    '''
    def __init__(self, tiles=None):
        self.free_tiles = tiles or []
        self.free_tiles = sorted(self.free_tiles)
        self.fixed_groups = []
        self.flowers = []
        self.last_tile = None

    def __repr__(self):
        if self.last_tile:
            last_tile_repr = repr(self.last_tile) + ' '
        else:
            last_tile_repr = ''
        return '%s%s %s %s' % (last_tile_repr, self.free_tiles, self.fixed_groups, self.flowers)

    def __eq__(self, other):
        # convert free_tiles to multiset
        my_free_tiles = Counter(self.free_tiles)
        other_free_tiles = Counter(other.free_tiles)
        if self.last_tile:
            my_free_tiles[self.last_tile] += 1
        if other.last_tile:
            other_free_tiles[other.last_tile] += 1

        return (my_free_tiles == other_free_tiles and
                Counter(self.fixed_groups) == Counter(other.fixed_groups) and
                Counter(self.flowers) == Counter(other.flowers))

    def clone(self):
        hand = Hand()
        hand.last_tile = self.last_tile
        hand.free_tiles = copy.copy(self.free_tiles)
        hand.flowers = copy.copy(self.flowers)
        for group in self.fixed_groups:
            hand.fixed_groups.append(group.clone())
        return hand

    def clear(self):
        del self.free_tiles[:]
        del self.fixed_groups[:]
        del self.flowers[:]
        self.last_tile = None

    def move_last_tile(self):
        last_tile = self.last_tile
        if self.last_tile:
            self.add_free_tile(self.last_tile)
            self.last_tile = None
        return last_tile

    def remove_last_tile(self):
        last_tile = self.last_tile
        self.last_tile = None
        return last_tile

    def add_free_tile(self, tile):
        bisect.insort(self.free_tiles, tile)

    def add_free_tiles(self, tiles):
        for tile in tiles:
            self.add_free_tile(tile)

    def remove_free_tile(self, tile):
        i = utils.index(self.free_tiles, tile)
        if i < 0:
            raise ValueError('%s is not in the hand' % tile)
        del self.free_tiles[i]

    def count(self, tile, last_tile=True, free_tiles=True, fixed_groups=False):
        count = 0
        if last_tile and self.last_tile == tile:
            count += 1

        if free_tiles:
            idx = utils.index(self.free_tiles, tile)
            if idx >= 0:
                while idx < len(self.free_tiles) and self.free_tiles[idx] == tile:
                    count += 1
                    idx += 1

        if fixed_groups:
            for group in self.fixed_groups:
                count += group.tiles.count(tile)

        return count

    def contains(self, tile, last_tile=True, free_tiles=True, fixed_groups=False,
                 flowers=False):
        if last_tile and self.last_tile == tile:
            return True

        if free_tiles and utils.index(self.free_tiles, tile) >= 0:
            return True

        if fixed_groups:
            for group in self.fixed_groups:
                if tile in group.tiles:
                    return True

        if flowers and tile in self.flowers:
            return True

        return False

    def add_flower(self, tile):
        self.flowers.append(tile)

    def move_flowers(self):
        # move flowers in free_tiles to self.flowers
        for tile in self.free_tiles:
            if tile.is_general_flower():
                self.add_flower(tile)
        self.free_tiles = filter(lambda x: not x.is_general_flower(), self.free_tiles)

        # if last_tile is flower, move it to self.flowers
        if self.last_tile and self.last_tile.is_general_flower():
            self.add_flower(self.last_tile)
            self.last_tile = None

    def discard(self, tile=None):
        tile = tile or self.last_tile
        if self.last_tile == tile:
            self.last_tile = None
        else:
            self.remove_free_tile(tile)
            self.move_last_tile()

    def num_kongs(self, exposed=True, concealed=True):
        count = 0
        for group in self.fixed_groups:
            if exposed and group.group_type == TileGroup.KONG_EXPOSED:
                count += 1
            elif concealed and group.group_type == TileGroup.KONG_CONCEALED:
                count += 1
        return count

    def num_pongs(self):
        count = 0
        for group in self.fixed_groups:
            if group.group_type == TileGroup.PONG:
                count += 1
        return count

    def num_chows(self):
        count = 0
        for group in self.fixed_groups:
            if group.group_type == TileGroup.CHOW:
                count += 1
        return count

    def chow(self, free_tiles, incoming_tile):
        return self._meld(free_tiles, incoming_tile, TileGroup.CHOW)

    def pong(self, incoming_tile):
        free_tiles = [incoming_tile, incoming_tile]
        return self._meld(free_tiles, incoming_tile, TileGroup.PONG)

    def kong_from_other(self, incoming_tile):
        free_tiles = [incoming_tile, incoming_tile, incoming_tile]
        return self._meld(free_tiles, incoming_tile, TileGroup.KONG_EXPOSED)

    def kong_from_self(self):
        if self.last_tile:
            pong_group = self._find_pong_group(self.last_tile)
            if pong_group:
                # appended kong
                pong_group.group_type = TileGroup.KONG_EXPOSED
                pong_group.tiles.append(self.last_tile)
                self.last_tile = None
                return pong_group
            else:
                # concealed kong
                free_tiles = [self.last_tile, self.last_tile, self.last_tile]
                group = self._meld(free_tiles, self.last_tile, TileGroup.KONG_CONCEALED)
                self.last_tile = None
                return group
        raise ValueError('Not kongable from self: No last tile')

    def get_chow_combs(self, incoming_tile):
        '''
        Get a list of tile pairs that form a chow with incoming_tile.

        For example, for an incoming tile CHAR2, the returned value could be
        [(Tile.CHAR1, Tile.CHAR3), (Tile.CHAR3, Tile.CHAR4)].

        '''
        combs = []
        if incoming_tile.is_honor() or incoming_tile.is_general_flower():
            return combs
        num = incoming_tile.tile_id % 16
        if num > 2:
            t1 = Tile.ALL[incoming_tile.tile_id - 2]
            t2 = Tile.ALL[incoming_tile.tile_id - 1]
            if utils.index(self.free_tiles, t1) >= 0 and utils.index(self.free_tiles, t2) >= 0:
                combs.append((t1, t2))
        if num > 1 and num < 9:
            t1 = Tile.ALL[incoming_tile.tile_id - 1]
            t2 = Tile.ALL[incoming_tile.tile_id + 1]
            if utils.index(self.free_tiles, t1) >= 0 and utils.index(self.free_tiles, t2) >= 0:
                combs.append((t1, t2))
        if num < 8:
            t1 = Tile.ALL[incoming_tile.tile_id + 1]
            t2 = Tile.ALL[incoming_tile.tile_id + 2]
            if utils.index(self.free_tiles, t1) >= 0 and utils.index(self.free_tiles, t2) >= 0:
                combs.append((t1, t2))
        return combs

    def can_chow(self, incoming_tile):
        return bool(self.get_chow_combs(incoming_tile))

    def can_pong(self, incoming_tile):
        idx = utils.index(self.free_tiles, incoming_tile)
        return (idx >= 0 and idx < len(self.free_tiles) - 1 and
                self.free_tiles[idx + 1] == incoming_tile)

    def can_kong(self, incoming_tile):
        '''Can this hand kong with a tile discarded by another player?'''
        idx = utils.index(self.free_tiles, incoming_tile)
        return (idx >= 0 and idx < len(self.free_tiles) - 2 and
               self.free_tiles[idx + 1] == incoming_tile and
               self.free_tiles[idx + 2] == incoming_tile)

    def can_self_kong(self):
        '''Can this hand kong with a tile drawn by itself?'''
        return self.can_appended_kong() or self.can_concealed_kong()

    def can_appended_kong(self):
        '''Can this hand make an appended kong?'''
        if self.last_tile:
            return bool(self._find_pong_group(self.last_tile))
        return False

    def can_concealed_kong(self):
        '''Can this hand make a conealed kong?'''
        if self.last_tile:
            return self.can_kong(self.last_tile)
        return False

    def can_win(self, incoming_tile=None):
        '''
        Determine if this hand + an incoming tile can win.

        If incoming_tile is None, hand.last_tile is used.

        '''
        incoming_tile = incoming_tile or self.last_tile
        tiles = copy.copy(self.free_tiles)
        if incoming_tile:
            bisect.insort(tiles, incoming_tile)

        table = self._construct_hand_table(tiles)
        num_3x = 0
        num_3x_plus_2 = 0
        for row in table:
            remainder = row[0] % 3
            if remainder == 0:
                num_3x += 1
            elif remainder == 2:
                num_3x_plus_2 += 1
        if num_3x != 3 or num_3x_plus_2 != 1:
            return False

        for i in xrange(0, 4):
            is_honor = (i == 3)
            row = table[i]
            if row[0] % 3 == 0:
                if not self._can_group_as_3(row, is_honor):
                    return False
            else:  # assert row[0] % 3 == 2
                if not self._can_group_as_pair_and_3(row, is_honor):
                    return False

        return True

    def ready(self):
        '''Is it a ready hand?'''
        for tile in Tile.ALL.itervalues():
            if self.can_win(tile):
                return True
        return False

    def waiting_tiles(self):
        '''Get a list of tiles that can make this hand win.'''
        tiles = []
        for tile in Tile.ALL.itervalues():
            if self.can_win(tile):
                bisect.insort(tiles, tile)
        return tiles

    def _can_group_as_pair_and_3(self, row, is_honor):
        '''Can group tiles into (a pair) + (sequences and triplets)?'''
        for i in xrange(1, 10):
            if row[i] > 1:
                row[i] -= 2
                row[0] -= 2
                if self._can_group_as_3(row, is_honor):
                    return True
                row[i] += 2
                row[0] += 2
        return False

    def _can_group_as_3(self, row, is_honor):
        '''Can group tiles into sequences and triplets?'''
        if row[0] == 0:
            return True

        # find the first tile
        idx = -1
        for i in xrange(1, 10):
            if row[i] > 0:
                idx = i
                break

        # group a triplet
        if (row[idx] >= 3):
            # substract it
            row[idx] -= 3
            row[0] -= 3
            result = self._can_group_as_3(row, is_honor)
            # add it back
            row[idx] += 3
            row[0] += 3
            return result

        # group a sequence
        if (not is_honor) and idx < 8 and row[idx + 1] > 0 and row[idx + 2] > 0:
            # substract it
            row[idx] -= 1
            row[idx + 1] -= 1
            row[idx + 2] -= 1
            row[0] -= 3
            result = self._can_group_as_3(row, is_honor)
            # add it back
            row[idx] += 1
            row[idx + 1] += 1
            row[idx + 2] += 1
            row[0] += 3
            return result

        return False

    def _construct_hand_table(self, tiles):
        '''
        Create a 2-dimentional table T, such that
        T[i][0] = Number of tiles whose suit == i
        T[i][j] = Number of tiles whose suit == i and face value == j

        where i is the tile suit:
            0 - chars
            1 - circles
            2 - bamboos
            3 - honors

        and j is face value of the tile, for example, the face value of
        3-circle is 3. For honors, it's:
            1 - east
            2 - south
            3 - west
            4 - north
            5 - red
            6 - green
            7 - white

        This special structure is used by can_win() for speedup.

        '''
        table = [[0] * 10 for __ in xrange(4)]

        honor_indices = {
            Tile.EAST: 1,
            Tile.SOUTH: 2,
            Tile.WEST: 3,
            Tile.NORTH: 4,
            Tile.RED: 5,
            Tile.GREEN: 6,
            Tile.WHITE: 7
        }

        for tile in tiles:
            if tile.is_char():
                table[0][0] += 1
                table[0][tile.tile_id % 16] += 1
            elif tile.is_circle():
                table[1][0] += 1
                table[1][tile.tile_id % 16] += 1
            elif tile.is_bamboo():
                table[2][0] += 1
                table[2][tile.tile_id % 16] += 1
            elif tile.is_honor():
                table[3][0] += 1
                table[3][honor_indices[tile]] += 1

        return table

    def _meld(self, free_tiles, incoming_tile, group_type):
        for tile in free_tiles:
            idx = utils.index(self.free_tiles, tile)
            if idx < 0:
                raise ValueError('%s is not in the hand' % tile)
            del self.free_tiles[idx]

        grouped_tiles = sorted(list(free_tiles) + [incoming_tile])
        group = TileGroup(grouped_tiles, group_type)
        self.fixed_groups.append(group)
        return group

    def _find_pong_group(self, tile):
        triplet = [tile, tile, tile]
        for group in self.fixed_groups:
            if group.group_type == TileGroup.PONG and group.tiles == triplet:
                return group
        return None


class Wall(object):
    '''
    The mahjong wall, where players draw new tiles from.

    In a real world game, tiles are stacked into four walls. But we don't have
    to do that here. The wall is essentially a full list of tiles, and players
    draw tiles from the end of the list.

    '''
    def __init__(self, chars=True, circles=True, bamboos=True, honors=True,
                 flowers=True, rng=None):
        self.tiles = []
        self.chars = chars
        self.circles = circles
        self.bamboos = bamboos
        self.honors = honors
        self.flowers = flowers
        self.rng = rng or random
        self.reset()

    def __eq__(self, other):
        return self.tiles == other.tiles

    def __iter__(self):
        for tile in self.tiles:
            yield tile

    def clone(self):
        wall = Wall(chars=False, circles=False, bamboos=False, honors=False, flowers=False)
        wall.tiles = copy.copy(self.tiles)
        wall.rng = self.rng
        return wall

    def shuffle(self):
        self.rng.shuffle(self.tiles)

    def num_tiles(self):
        return len(self.tiles)

    def draw(self):
        try:
            return self.tiles.pop()
        except IndexError:
            return None

    def reset(self):
        del self.tiles[:]
        if self.chars:
            self._add_tiles(Tile.CHARS, 4)
        if self.circles:
            self._add_tiles(Tile.CIRCLES, 4)
        if self.bamboos:
            self._add_tiles(Tile.BAMBOOS, 4)
        if self.honors:
            self._add_tiles(Tile.HONORS, 4)
        if self.flowers:
            self._add_tiles(Tile.FLOWERS, 1)

    def _add_tiles(self, tiles, num_duplicates):
        for tile in tiles:
            for __ in xrange(num_duplicates):
                self.tiles.append(tile)


class GameSettings(object):
    '''
    A GameSettings instance stores variants of a games. It should be attached
    to a GameContext, and once attached, it should never change.

    '''
    def __init__(self):
        self._attrs = {
            'bloodmatch': False,            # fight until only one player left
            'declarable': True,             # be able to declare your hand is ready
            'max_dealer_defended': 999,     # maximum times you can defend your dealer position
            'multi_winners': False,         # multiple players can win on the same discarded tile
            'num_hand_tiles': 16,           # number of tiles of a hand
            'scorer': 'tw',                 # specifies how to score
            'tie_on_4_kongs': True,         # tie if there're four kongs on the table
            'tie_on_4_waiting': False,      # tie if four players declare ready
            'tie_on_winds': 'all',          # tie if four same winds are discarded at the beginning
            'tie_wall': 16,                 # number of tiles must be left in the wall
            'tie_wall_per_kong': 1,         # number of tiles that should be added
            'wall_bamboos': True,           # include bamboos in the wall
            'wall_chars': True,             # include characters in the wall
            'wall_circles': True,           # include circles in the wall
            'wall_flowers': True,           # include flowers in the wall
            'wall_honors': True,            # include honors in the wall
            'water': True,                  # enable water penalty

            # special winning patterns
            'patterns_win': [
                'seven-flowers',
                'eight-flowers'
            ],

            # pattern_name -> (score, score unit)
            'patterns_score': {
                'dealer': (1, 'tai'),
                'self-picked': (1, 'tai'),
                'purely-concealed': (1, 'tai'),
                'wind-seat': (1, 'tai'),
                'wind-round': (1, 'tai'),
                'dragons': (1, 'tai'),
                'flower-seat': (1, 'tai'),
                'waiting-for-one': (1, 'tai'),
                'robbed-kong': (1, 'tai'),
                'konged-or-flowered': (1, 'tai'),
                'last-tile-in-wall': (1, 'tai'),
                'all-melded': (2, 'tai'),
                'dealer-defended': (2, 'tai'),
                'four-flowers': (2, 'tai'),
                'three-concealed-triplets': (2, 'tai'),
                'all-sequences': (2, 'tai'),
                'purely-concealed-self-picked': (3, 'tai'),
                'all-pongs': (4, 'tai'),
                'flower-win-after-dealing': (4, 'tai'),
                'earth-ready': (4, 'tai'),
                'small-three-dragons': (4, 'tai'),
                'mix-a-suit': (4, 'tai'),
                'four-concealed-triplets': (5, 'tai'),
                'five-concealed-triplets': (8, 'tai'),
                'seven-flowers': (8, 'tai'),
                'eight-flowers': (8, 'tai'),
                'heaven-ready': (8, 'tai'),
                'human-win': (8, 'tai'),
                'small-four-winds': (8, 'tai'),
                'big-three-dragons': (8, 'tai'),
                'all-honors': (8, 'tai'),
                'same-suit': (8, 'tai'),
                'earth-win': (16, 'tai'),
                'big-four-winds': (16, 'tai'),
                'heaven-win': (24, 'tai')
            },

            # extra filters (restrictions) to win
            'patterns_win_filter': []
        }

    def __eq__(self, other):
        return self.__dict__.get('_attrs') == other.__dict__.get('_attrs')

    def __getattr__(self, name):
        try:
            # avoid self._attrs here, it causes recursion
            attrs = self.__dict__.get('_attrs')
            return attrs[name]
        except KeyError:
            raise AttributeError('Attribute `%s` not found' % name)

    def __setattr__(self, name, value):
        if name == '_attrs':
            self.__dict__[name] = value
        else:
            # avoid self._attrs here, it causes recursion
            attrs = self.__dict__.get('_attrs')
            if name not in attrs:
                raise AttributeError('Attribute `%s` not found')
            attrs[name] = value

    def total_tiles(self):
        total = 0
        if self.wall_bamboos:
            total += 36
        if self.wall_chars:
            total += 36
        if self.wall_circles:
            total += 36
        if self.wall_flowers:
            total += 8
        if self.wall_honors:
            total += 28
        return total


class Player(object):
    '''
    A Player consists of the following:
    * hand: A hand of tiles that the player is holding.
    * discarded: A list of tiles that the player discarded.
    * decision: A string that represents the player's decision.
    * extra: A dictionary that stores extra data.

    '''
    def __init__(self):
        self.hand = Hand()
        self.discarded = []
        self.decision = None
        self.extra = {}

    def __eq__(self, other):
        return (self.hand == other.hand and
                self.decision == other.decision and
                self.discarded == other.discarded and
                self.extra == other.extra)

    def reset(self):
        self.hand.clear()
        del self.discarded[:]
        self.decision = None
        self.extra.clear()

    def clone(self):
        p = Player()
        p.hand = self.hand.clone()
        p.discarded = copy.copy(self.discarded)
        p.decision = self.decision
        p.extra = copy.copy(self.extra)
        return p

    def discard(self, tile=None):
        tile = tile or self.hand.last_tile
        if tile is None:
            raise ValueError('Must specify a tile')
        self.hand.discard(tile)
        self.discarded.append(tile)


class GameContext(object):
    '''
    A GameContext is a snapshot during a game. Ideally, you're be able to
    resume a game from a game context.

    A GameContext has the following attributes:
    * state: State name. This determines what other attributes are available.
    * wall: The tile wall, available after 'wall-built' state.
    * players: A list of four players. [0..3] are east, south, west, and north
               in sequence.
    * discarded_pool: A list of discarded tiles.
    * cur_player_idx: An integer index specifying the current turn.
    * last_player_idx: An integer index specifying the last turn.
    * round: Round counter, 0-based.
    * match: Match counter, 0-based.
    * dealer: An integer index specifying who the dealer is.
    * dealer_defended: How many times does the dealer defend his dealer role?
    * winners: A list of integers specifying who won the game. Most of the
               time it has only one element unless multi_winners is on. It is
               set to None if it's a tie.
    * settings: A GameSettings instance.
    * extra: A dictionary for extra data.

    '''
    def __init__(self, settings=None):
        self.state = 'start'
        self.wall = None
        self.players = [Player() for __ in xrange(4)]
        self.discarded_pool = []
        self.cur_player_idx = 0
        self.last_player_idx = None
        self.round = 0
        self.match = 0
        self.dealer = 0
        self.dealer_defended = 0
        self.winners = None
        self.settings = settings or GameSettings()
        self.extra = {}

    def __eq__(self, other):
        return (self.state == other.state and
                self.wall == other.wall and
                self.players == other.players and
                self.discarded_pool == other.discarded_pool and
                self.cur_player_idx == other.cur_player_idx and
                self.last_player_idx == other.last_player_idx and
                self.round == other.round and
                self.match == other.match and
                self.dealer == other.dealer and
                self.dealer_defended == other.dealer_defended and
                self.winners == other.winners and
                self.settings == other.settings and
                self.extra == other.extra)

    def reset(self):
        self.state = 'start'
        self.wall = None
        for player in self.players:
            player.reset()
        del self.discarded_pool[:]
        self.cur_player_idx = 0
        self.last_player_idx = None
        self.round = 0
        self.match = 0
        self.dealer = 0
        self.dealer_defended = 0
        self.winners = None
        self.extra.clear()

    def clone(self):
        c = GameContext()
        c.state = self.state
        c.wall = self.wall.clone() if self.wall else None
        c.players = [p.clone() for p in self.players] if self.players else None
        c.discarded_pool = copy.copy(self.discarded_pool)
        c.cur_player_idx = self.cur_player_idx
        c.last_player_idx = self.last_player_idx
        c.round = self.round
        c.match = self.match
        c.dealer = self.dealer
        c.dealer_defended = self.dealer_defended
        c.winners = self.winners
        c.settings = self.settings
        c.extra = copy.copy(self.extra)
        return c

    def player(self, offset=0):
        '''Get a player based on the current player.'''
        if self.cur_player_idx is None:
            return None
        idx = (self.cur_player_idx + offset) % 4
        return self.players[idx]

    def reset_players(self):
        for player in self.players:
            player.reset()

    def is_tie(self, cur_state=True, four_waiting=True, four_kongs=True,
               wall_tie=True, four_winds=True):
        '''
        Return if this context meets the 'tie' condition.

        There are many ways to conduct a tie. This method provides the
        following keyword arguments for you to switch off some of the tie
        scenarios.

        :param cur_state: Check for current state?
        :param four_waiting: Check for 4-waiting tie?
        :param four_kongs: Check for 4-kong tie?
        :param wall_tie: Check for wall tie?
        :param four_winds: Check for 4-wind tie?

        '''
        # already a tie
        if cur_state and self.state == 'end' and not self.winners:
            return True

        # 4-waiting tie
        if four_waiting and self.settings.tie_on_4_waiting:
            ready_players = filter(lambda player: player.extra.get('declared_ready'),
                                   [player for player in self.players])
            if len(ready_players) > 3:
                return True

        # count number of kongs on the table
        total_kongs = 0
        for player in self.players:
            total_kongs += player.hand.num_kongs()

        # 4-kong tie
        if four_kongs and self.settings.tie_on_4_kongs and total_kongs > 3:
            return True

        # wall tie
        if wall_tie:
            # number of tiles that should be left in the wall
            min_num_tiles = self.settings.tie_wall + total_kongs * self.settings.tie_wall_per_kong
            if self.wall.num_tiles() <= min_num_tiles:
                return True

        # wind tie
        if four_winds and self.settings.tie_on_winds:
            # get the first discarded tiles from each player
            discarded = [p.discarded[0] if p.discarded else None for p in self.players]
            if self.settings.tie_on_winds == 'west':
                # all players discard west wind on initial discarding
                if len(filter(lambda x: x == Tile.WEST, discarded)) == 4:
                    return True
            else:
                # assert self.settings.tie_on_winds == 'all'
                # all players discard the same wind on initial discarding
                if discarded[0] and discarded[0].is_wind() and \
                   discarded[0] == discarded[1] and \
                   discarded[1] == discarded[2] and \
                   discarded[2] == discarded[3]:
                    return True

        return False

    def discard(self, tile, player_idx=None):
        if player_idx is None:
            player_idx = self.cur_player_idx

        self.players[player_idx].discard(tile)
        self.discarded_pool.append(tile)

    def last_discarded(self):
        if self.discarded_pool:
            return self.discarded_pool[-1]
        return None

    def remove_last_discarded(self, player_offset=0):
        player = self.player(player_offset)
        if self.discarded_pool and player.discarded:
            tile1 = self.discarded_pool[-1]
            tile2 = player.discarded[-1]
            if tile1 == tile2:
                self.discarded_pool.pop()
                player.discarded.pop()
                return tile1
        return None

    def next_turn(self):
        if self.cur_player_idx is None:
            self.cur_player_idx = 0
            self.last_player_idx = None
        else:
            self.set_turn((self.cur_player_idx + 1) % 4)

    def set_turn(self, player_idx):
        self.last_player_idx = self.cur_player_idx
        self.cur_player_idx = player_idx
