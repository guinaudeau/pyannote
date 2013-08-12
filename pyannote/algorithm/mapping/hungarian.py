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
from base import BaseMapper
from pyannote.base.mapping import OneToOneMapping
from pyannote.base.matrix import get_cooccurrence_matrix

class HungarianMapper(BaseMapper):
    """One-to-one label mapping based on the Hungarian algorithm

    The `Hungarian` mapper relies on the Hungarian algorithm [1]_ to find the
    one-to-one mapping M between labels of two annotations `A` and `B` that
    maximizes ∑ K(a, M(a)) where `cost` function K(a, b) typically is the
    cooccurrence duration of labels a and b.

    Parameters
    ----------
    cost : func
        This parameter controls how K is computed.
        Defaults to :class:`pyannote.base.matrix.get_cooccurrence_matrix`,
        i.e. total cooccurence duration

    Examples
    --------

        >>> from pyannote import Segment, Annotation

        >>> A = Annotation(modality='A')
        >>> A[Segment(0, 4)] = 'a1'
        >>> A[Segment(4, 15)] = 'a2'
        >>> A[Segment(15, 17)] = 'a3'
        >>> A[Segment(17, 25)] = 'a1'
        >>> A[Segment(23, 30)] = 'a2'

        >>> B = Annotation(modality='B')
        >>> B[Segment(0, 10)] = 'b1'
        >>> B[Segment(10, 15)] = 'b2'
        >>> B[Segment(14, 20)] = 'b1'
        >>> B[Segment(23, 30)] = 'b2'

        >>> mapper = HungarianMapper()
        >>> mapping = mapper(A, B)
        >>> print mapping
        (
           a1 <--> b1
           a2 <--> b2
           a3 <-->
        )


    References
    ----------
.. [1] "Hungarian algorithm", http://en.wikipedia.org/wiki/Hungarian_algorithm

    See Also
    --------
    pyannote.base.matrix.get_cooccurrence_matrix
    pyannote.base.matrix.get_tfidf_matrix
    pyannote.base.matrix.LabelMatrix

    """
    def __init__(self, cost=None):
        super(HungarianMapper, self).__init__()

        # Hungarian association solver / Munkres algorithm
        self.__munkres = Munkres()

        # By default, uses label cooccurrence duration
        if cost is None:
            cost = get_cooccurrence_matrix
        self.__cost = cost

    def _associate(self, A, B):

        # Cooccurrence matrix
        matrix = self.__cost(A, B)
        M = OneToOneMapping(A.modality, B.modality)

        # Shape and labels
        nRows, nCols = matrix.shape
        rows = matrix.get_rows()
        cols = matrix.get_columns()

        # Cost matrix
        N = max(nCols, nRows)
        C = np.zeros((N, N))
        C[:nCols, :nRows] = (np.max(matrix.values) - matrix.values).T

        # Optimal one-to-one mapping
        mapping = self.__munkres.compute(C)

        for b, a in mapping:
            if (b < nCols) and (a < nRows):
                if matrix.loc[rows[a], cols[b]] > 0:
                    M += ([rows[a]], [cols[b]])

        # A --> NoMatch
        for alabel in set(rows)-M.left_set:
            M += ([alabel], None)

        # NoMatch <-- B
        for blabel in set(cols)-M.right_set:
            M += (None, [blabel])

        return M


if __name__ == "__main__":
    import doctest
    doctest.testmod()
