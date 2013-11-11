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

import itertools

import numpy as np
import scipy.signal

from pyannote import Timeline
from pyannote.base.segment import Segment, SlidingWindow
from pyannote.stats.gaussian import Gaussian


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.izip(a, b)


class SlidingWindowsSegmentation(object):
    """

    <---d---><-g-><---d--->
    [   L   ]     [   R   ]
         [   L   ]     [   R   ]
    <-s->

    Parameters
    ----------
    duration : float, optional
        Set left/right window duration. Defaults to 1 second.
    step : float, optional
        Set step duration. Defaults to 100ms
    gap : float, optional
        Set gap duration. Defaults to no gap (i.e. 0 second)
    """

    def __init__(self, duration=1.0, step=0.1, gap=0.0, threshold=0.):
        super(SlidingWindowsSegmentation, self).__init__()
        self.duration = duration
        self.step = step
        self.gap = gap
        self.threshold = threshold

    def diff(self, left, right, feature):
        """Compute difference between left and right windows

        Parameters
        ----------
        left, right : Segment
            Left and right windows
        feature : SlidingWindowFeature
            Pre-extracted features

        Returns
        -------
        d : float
            Difference value (the higher, the more different)
        """
        raise NotImplementedError(
            'You must inherit from SlidingWindowSegmentation')

    def iterdiff(self, feature):
        """(middle, difference) generator

        `middle`
        `difference`


        Parameters
        ----------
        feature : SlidingWindowFeature
            Pre-extracted features
        """

        #
        focus = feature.getExtent()

        sliding_window = SlidingWindow(
            duration=self.duration,
            step=self.step,
            start=focus.start, end=focus.end)

        for left in sliding_window:

            right = Segment(
                start=left.end,
                end=left.end + self.duration + self.gap
            )
            middle = .5*(left.end + right.start)

            yield middle, self.diff(left, right, feature)

    def apply(self, feature):

        x, y = zip(*[
            (m, d) for m, d in self.iterdiff(feature)
        ])
        x = np.array(x)
        y = np.array(y)

        # find local maxima
        maxima = scipy.signal.argrelmax(y)
        x = x[maxima]
        y = y[maxima]

        # only keep high enough local maxima
        high_maxima = np.where(y > self.threshold)

        # create list of segment boundaries
        # do not forget very first and last boundaries
        extent = feature.getExtent()
        boundaries = itertools.chain(
            [extent.start], x[high_maxima], [extent.end]
        )

        # create list of segments from boundaries
        segments = [Segment(*p) for p in pairwise(boundaries)]

        # TODO: find a way to set 'uri'
        return Timeline(segments=segments, uri=None)


class GaussianDivergenceSegmentation(SlidingWindowsSegmentation):

    def __init__(
        self,
        duration=1., step=0.1, gap=0., threshold=0.
    ):

        super(GaussianDivergenceSegmentation, self).__init__(
            duration=duration, step=step, gap=gap, threshold=threshold
        )

    def diff(self, left, right, feature):

        gl = Gaussian(covariance_type='diag')
        Xl = feature.crop(left)
        gl.fit(Xl)

        gr = Gaussian(covariance_type='diag')
        Xr = feature.crop(right)
        gr.fit(Xr)

        try:
            divergence = gl.divergence(gr)
        except:
            divergence = np.NaN

        return divergence
