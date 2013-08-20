#!/usr/bin/env python
# encoding: utf-8

# Copyright 2012-2013 Herve BREDIN (bredin@limsi.fr)

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

from pyannote.base.mapping import ManyToOneMapping
from pyannote.base.matrix import get_cooccurrence_matrix
from base import BaseMapper
import numpy as np


class ConservativeDirectMapper(BaseMapper):
    """
    Maps left label a to right label b if b is the only one cooccurring with a.
    """
    def __init__(self):
        super(ConservativeDirectMapper, self).__init__()

    def _associate(self, A, B):
        # TODO : make it much simpler

        # Cooccurrence matrix
        matrix = get_cooccurrence_matrix(A, B)

        # For each row, find the most frequent cooccurring column
        pairs = matrix.argmax(axis=1)

        # and keep this pair only if there is no ambiguity
        pairs = {a: b for a, b in pairs.iteritems()
                 if np.sum((matrix.subset(rows=set([a])) > 0).df.values) == 1}

        # Reverse dict and group alabels by argmax
        sriap = {}
        for a, b in pairs.iteritems():
            if b not in sriap:
                sriap[b] = set([])
            sriap[b].add(a)

        M = ManyToOneMapping(A.modality, B.modality)

        for b, a_s in sriap.iteritems():
            M += (a_s, [b])

        rows = matrix.get_rows()
        cols = matrix.get_columns()

        for a in set(rows)-M.left_set:
            M += ([a], None)

        for b in set(cols)-M.right_set:
            M += (None, [b])

        return M


class ArgMaxMapper(BaseMapper):
    """Many-to-one label mapping based on cost function.

    The `ArgMax` mapper relies on a cost function K to find the
    many-to-one mapping M between labels of two annotations `A` and `B` such
    that M(a) = argmax K(a, b).

    `cost` function K(a, b) typically is the total cooccurrence duration of
    labels a and b.

    Parameters
    ----------
    cost : func
        This parameter controls how K is computed.
        Defaults to `pyannote.base.matrix.get_cooccurrence_matrix`,
        i.e. total cooccurence duration

    Examples
    --------

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


    See Also
    --------
    pyannote.base.matrix.get_cooccurrence_matrix
    pyannote.base.matrix.get_tfidf_matrix
    pyannote.base.matrix.LabelMatrix

    """
    def __init__(self, cost=None):
        super(ArgMaxMapper, self).__init__()
        if cost is None:
            cost = get_cooccurrence_matrix
        self.__cost = cost

    def _associate(self, A, B):

        # Cooccurrence matrix
        matrix = self.__cost(A, B)

        # argmax
        pairs = matrix.argmax(axis=1)
        pairs = {a: b for a, b in pairs.iteritems() if matrix[a, b] > 0}

        # Reverse dict and group alabels by argmax
        sriap = {}
        for a, b in pairs.iteritems():
            if b not in sriap:
                sriap[b] = set([])
            sriap[b].add(a)

        M = ManyToOneMapping(A.modality, B.modality)

        for b, a_s in sriap.iteritems():
            M += (a_s, [b])

        rows = matrix.get_rows()
        cols = matrix.get_columns()
        for a in set(rows)-M.left_set:
            M += ([a], None)
        for b in set(cols)-M.right_set:
            M += (None, [b])

        return M

if __name__ == "__main__":
    import doctest
    doctest.testmod()
