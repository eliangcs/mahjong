import unittest

from mahjong import scoring
from mahjong.patterns import MatchResult


class TestTWScorer(unittest.TestCase):

    def test_tw_scorer(self):
        match_results = {
            'dealer': MatchResult(1, 1),
            'dealer-defended': MatchResult(1, 3),
            'purely-concealed': MatchResult((1, 2, 3), 1),
            'dragons': MatchResult((1, 2, 3), 2),
            'four-flowers': MatchResult((1, 2), 2),
            'seven-flowers': MatchResult(3, 1),
        }
        patterns_score = {
            'dealer': (1, 'tai'),
            'dealer-defended': (2, 'tai'),
            'purely-concealed': (1, 'tai'),
            'dragons': (1, 'tai'),
            'four-flowers': (2, 'tai'),
            'seven-flowers': (8, 'tai')
        }

        # dealer:           [0, 1, 0, 0] x 1 = [0, 1, 0, 0]
        # dealer-defended:  [0, 3, 0, 0] x 2 = [0, 6, 0, 0]
        # purely-concealed: [0, 1, 1, 1] x 1 = [0, 1, 1, 1]
        # dragons:          [0, 2, 2, 2] x 1 = [0, 2, 2, 2]
        # four-flowers:     [0, 2, 2, 0] x 2 = [0, 4, 4, 0]
        # seven-flowers:    [0, 0, 0, 1] x 8 = [0, 0, 0, 8]
        #----------------------------------------------------
        # total:                              [0, 14, 7, 11]
        scores = scoring.score('tw', match_results, patterns_score)
        self.assertEqual(scores, [0, 14, 7, 11])
