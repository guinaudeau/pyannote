#!/usr/bin/env python
# encoding: utf-8

# Copyright 2012-2014 CNRS (Herve BREDIN -- bredin@limsi.fr)

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


from base import BaseMetric
from pyannote.base.annotation import Annotation

PTY_NAME = 'segmentation purity'
CVG_NAME = 'segmentation coverage'
TOTAL = 'total'
INTER = 'intersection' 

class SegmentationCoverage(BaseMetric):
    """Segmentation coverage

    >>> from pyannote import Timeline, Segment
    >>> from pyannote.metric.segmentation import SegmentationCoverage
    >>> cvg = SegmentationCoverage()

    >>> reference = Timeline()
    >>> reference.add(Segment(0, 1))
    >>> reference.add(Segment(1, 2))
    >>> reference.add(Segment(2, 4))

    >>> hypothesis = Timeline()
    >>> hypothesis.add(Segment(0, 4))
    >>> cvg(reference, hypothesis)
    1.0

    >>> hypothesis = Timeline()
    >>> hypothesis.add(Segment(0, 3))
    >>> hypothesis.add(Segment(3, 4))
    >>> cvg(reference, hypothesis)
    0.75
    """

    @classmethod
    def metric_name(cls):
        return CVG_NAME

    @classmethod
    def metric_components(cls):
        return [TOTAL, INTER]

    def _get_details(self, reference, hypothesis, **kwargs):

        if isinstance(reference, Annotation):
            reference = reference.get_timeline()

        if isinstance(hypothesis, Annotation):
            hypothesis = hypothesis.get_timeline()

        detail = self._init_details()

        prev_r = None
        duration = 0.
        intersection = 0.
        for r, h in reference.co_iter(hypothesis):
        
            if r != prev_r:
                detail[TOTAL] += duration
                detail[INTER] += intersection
        
                duration = r.duration
                intersection = 0.
                prev_r = r
        
            intersection = max(intersection, (r & h).duration)

        detail[TOTAL] += duration
        detail[INTER] += intersection
        
        return detail

    def _get_rate(self, detail):

        return detail[INTER] / detail[TOTAL]

    def _pretty(self, detail):
        string = ""
        string += "  - duration: %.2f seconds\n" % (detail[TOTAL])
        string += "  - correct: %.2f seconds\n" % (detail[INTER])
        string += "  - %s: %.2f %%\n" % (self.name, 100*detail[self.name])
        return string

class SegmentationPurity(SegmentationCoverage):
    """Segmentation purity

    >>> from pyannote import Timeline, Segment
    >>> from pyannote.metric.segmentation import SegmentationPurity
    >>> pty = SegmentationPurity()

    >>> reference = Timeline()
    >>> reference.add(Segment(0, 1))
    >>> reference.add(Segment(1, 2))
    >>> reference.add(Segment(2, 4))

    >>> hypothesis = Timeline()
    >>> hypothesis.add(Segment(0, 1))
    >>> hypothesis.add(Segment(1, 2))
    >>> hypothesis.add(Segment(2, 3))
    >>> hypothesis.add(Segment(3, 4))
    >>> pty(reference, hypothesis)
    1.0

    >>> hypothesis = Timeline()
    >>> hypothesis.add(Segment(0, 4))
    >>> pty(reference, hypothesis)
    0.5

    """


    @classmethod
    def metric_name(cls):
        return PTY_NAME

    def _get_details(self, reference, hypothesis, **kwargs):
        return super(SegmentationPurity, self)._get_details(
            hypothesis, reference, **kwargs
        )


if __name__ == "__main__":
    import doctest
    doctest.testmod()
