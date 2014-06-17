def score(scorer_name, match_results, patterns_score):
    scorer = _SCORERS.get(scorer_name)
    if not scorer:
        raise KeyError('Scorer `%s` not found' % scorer_name)
    return scorer.score(match_results, patterns_score)


class Scorer(object):

    def score(self, match_results, patterns_score):
        '''
        Return an array [S0, S1, S2, S3], where Si is the score that player i
        loses. The definition of "score" is determined by the subclass.

        :param match_results: A dictionary whose keys are pattern names and
                              values are MatchResults.
        :param patterns_score: A dictionary whose keys are pattern names and
                               values are tuples of (score, score unit). This
                               is the same as ``GameSettings.patterns_score``.

        '''
        raise NotImplementedError


class TWScorer(Scorer):

    def score(self, match_results, patterns_score):
        result = [0, 0, 0, 0]
        for pattern_name, match_result in match_results.iteritems():
            pattern_score, __ = patterns_score.get(pattern_name)
            for i in xrange(0, 4):
                result[i] += match_result.get(i) * pattern_score
        return result


class JPScorer(Scorer):

    def score(self, match_results, patterns_score):
        # TODO
        raise NotImplementedError


_SCORERS = {
    'tw': TWScorer(),
    'jp': JPScorer()
}
