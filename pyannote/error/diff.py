#!/usr/bin/env python
# encoding: utf-8

# Copyright 2012 Herve BREDIN (bredin@limsi.fr)

# This file is part of PyAnnote.
#
#     PyAnnote is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     PyAnnote is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with PyAnnote.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np
from munkres import Munkres

from pyannote.metric.identification import UnknownIDMatcher
from pyannote.base.annotation import Annotation

from pyannote.metric.identification import IER_CORRECT, \
    IER_CONFUSION, \
    IER_FALSE_ALARM, \
    IER_MISS

REGRESSION = 'regression'
IMPROVEMENT = 'improvement'
BOTH_CORRECT = 'both_correct'
BOTH_INCORRECT = 'both_incorrect'


class Diff(object):

    def __init__(self, matcher=None, unknown=True):

        super(Diff, self).__init__()

        if matcher:
            self.matcher = matcher
        else:
            self.matcher = UnknownIDMatcher()
        self.unknown = unknown
        self.munkres = Munkres()

    def compare(self, reference, hypothesis, correct=True):
        """

        Returns
        -------
        diff : `Annotation`
            Annotation containing list of errors ()

        """

        # common (up-sampled) timeline
        common_timeline = reference.timeline + hypothesis.timeline
        common_timeline = common_timeline.segmentation()

        # align reference on common timeline
        R = reference >> common_timeline

        # translate and align hypothesis on common timeline
        H = hypothesis >> common_timeline

        self.diff = Annotation(uri=reference.uri, modality=reference.modality)

        # loop on all segments
        for segment in common_timeline:

            # # segment duration
            # duration = segment.duration

            # list of IDs in reference segment
            rlabels = R.get_labels(segment, unknown=self.unknown, unique=False)

            # list of IDs in hypothesis segment
            hlabels = H.get_labels(segment, unknown=self.unknown, unique=False)

            _, details = self.matcher.manyToManyMatch(rlabels, hlabels)

            if correct:
                for r, h in details[IER_CORRECT]:
                    track = self.diff.new_track(segment, candidate=IER_CORRECT, prefix=IER_CORRECT)
                    self.diff[segment, track] = (IER_CORRECT, r, h)

            for r, h in details[IER_CONFUSION]:
                track = self.diff.new_track(segment, candidate=IER_CONFUSION, prefix=IER_CONFUSION)
                self.diff[segment, track] = (IER_CONFUSION, r, h)

            for r in details[IER_MISS]:
                track = self.diff.new_track(segment, candidate=IER_MISS, prefix=IER_MISS)
                self.diff[segment, track] = (IER_MISS, r, None)

            for h in details[IER_FALSE_ALARM]:
                track = self.diff.new_track(segment, candidate=IER_FALSE_ALARM, prefix=IER_FALSE_ALARM)
                self.diff[segment, track] = (IER_FALSE_ALARM, None, h)

        return self.diff.copy()

    def _match_errors(self, old_error, new_error):
        old_type, old_ref, old_hyp = old_error
        new_type, new_ref, new_hyp = new_error
        return (old_ref == new_ref) * ((old_type == new_type) + (old_hyp == new_hyp))

    def regression(self, reference, old_hypothesis, new_hypothesis):

        reference = reference.smooth()
        old_hypothesis = old_hypothesis.smooth()
        new_hypothesis = new_hypothesis.smooth()
        old_diff = self.compare(reference, old_hypothesis, correct=True).smooth()
        new_diff = self.compare(reference, new_hypothesis, correct=True).smooth()
        common_timeline = (old_diff.timeline + new_diff.timeline).segmentation()
        old_diff = old_diff >> common_timeline
        new_diff = new_diff >> common_timeline

        regression = Annotation(uri=reference.uri, modality=reference.modality)

        for segment in common_timeline:

            old_errors = old_diff.get_labels(segment, unique=False)
            new_errors = new_diff.get_labels(segment, unique=False)

            n1 = len(old_errors)
            n2 = len(new_errors)
            n = max(n1, n2)

            match = np.zeros((n, n), dtype=int)
            for i1, e1 in enumerate(old_errors):
                for i2, e2 in enumerate(new_errors):
                    match[i1, i2] = self._match_errors(e1, e2)

            mapping = self.munkres.compute(2-match)

            for i1, i2 in mapping:

                if i1 >= n1:
                    track = regression.new_track(segment, candidate=REGRESSION, prefix=REGRESSION)
                    regression[segment, track] = (REGRESSION, None, new_errors[i2])

                elif i2 >= n2:
                    track = regression.new_track(segment, candidate=IMPROVEMENT, prefix=IMPROVEMENT)
                    regression[segment, track] = (IMPROVEMENT, old_errors[i1], None)

                elif old_errors[i1][0] == IER_CORRECT:

                    if new_errors[i2][0] == IER_CORRECT:
                        track = regression.new_track(segment, candidate=BOTH_CORRECT, prefix=BOTH_CORRECT)
                        regression[segment, track] = (BOTH_CORRECT, old_errors[i1], new_errors[i2])

                    else:
                        track = regression.new_track(segment, candidate=REGRESSION, prefix=REGRESSION)
                        regression[segment, track] = (REGRESSION, old_errors[i1], new_errors[i2])

                else:

                    if new_errors[i2][0] == IER_CORRECT:
                        track = regression.new_track(segment, candidate=IMPROVEMENT, prefix=IMPROVEMENT)
                        regression[segment, track] = (IMPROVEMENT, old_errors[i1], new_errors[i2])

                    else:
                        track = regression.new_track(segment, candidate=BOTH_INCORRECT, prefix=BOTH_INCORRECT)
                        regression[segment, track] = (BOTH_INCORRECT, old_errors[i1], new_errors[i2])

        return regression.smooth()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
