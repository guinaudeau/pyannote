#!/usr/bin/env python
# encoding: utf-8

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

import numpy as np


def dtw(source, target, window, distance):

    n = len(source)
    m = len(target)
    window = max(window, abs(n-m))

    D = np.inf * np.ones((n, m))
    D[0, 0] = 0

    for i in range(1, n):
        for j in range(max(1, i-window), min(m, i+window)):
            cost = distance(source[i], target[j])
            D[i, j] = cost + min(D[i-1, j], D[i, j-1], D[i-1, j-1])

    i = n-1
    j = m-1

    path = [(i, j)]
    d = D[-1, -1]
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            if D[i-1, j-1] <= d:
                d = D[i-1, j-1]
                new_i = i-1
                new_j = j-1
        if i > 0:
            if D[i-1, j] <= d:
                d = D[i-1, j]
                new_i = i-1
                new_j = j
        if j > 0:
            if D[i, j-1] <= d:
                d = D[i, j-1]
                new_i = i
                new_j = j-1

        path.append((new_i, new_j))
        i = new_i
        j = new_j

    return D, path[::-1]


def align(source, target, step=1.):
    """

    Parameters
    ----------
    source, target : Timeline

    step : float

    """
    pass
