#!/usr/bin/env python
# encoding: utf-8

# Copyright 2013 Claude BARRAS (barras@limsi.fr)
# Copyright 2013 Herve BREDIN (bredin@limsi.fr)

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


import scipy.stats
import numpy as np
from pyannote.base.feature import SlidingWindowFeature
from pyannote.base.segment import Segment


def _warp(x, w):
    """
    Apply feature warping using sliding window
    NB: C implementation is more than 10x faster...

    Parameters:
    ----------
    x : ndarray (nb_frames, dim_frame)
        features
    w : int
        size of sliding window (nb_frames)

    """

    # number of samples
    n = len(x)

    if w > 0 and n > w:

        # lookup table
        table = scipy.stats.norm.ppf((np.arange(w) + 0.5) / w)

        # initalize
        y = np.zeros_like(x)

        # first w/2 vectors
        a = np.argsort(np.argsort(x[0:w, :], 0), 0)
        y[0:w/2, :] = table[a[0:w/2, :]]

        # n-w middle vectors using sliding window
        for i in range(0, n-w):
            a = np.argsort(np.argsort(x[i+1:i+1+w, :], 0), 0)
            y[i+w/2, :] = table[a[w/2-1]]

        # last w/2 vectors
        a = np.argsort(np.argsort(x[n-w:n, :], 0), 0)
        y[n-w/2:n, :] = table[a[w/2:w, :]]

    else:
        # perform global warping
        table = scipy.stats.norm.ppf((np.arange(n) + 0.5) / n)
        y = table[np.argsort(np.argsort(x, 0), 0)]

    return y


def warp(features, window):
    """
    Parameters
    ----------
    features : SlidingWindowFeature
    window : float
        Duration of warping window in seconds
    """

    x = features.data
    _, w = features.sliding_window.segmentToRange(
        Segment(start=0., end=window))

    y = _warp(x, w)

    return SlidingWindowFeature(y, features.sliding_window)
