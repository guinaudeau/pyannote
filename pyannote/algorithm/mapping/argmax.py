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

from pyannote.base.mapping import ManyToOneMapping
from pyannote.base.matrix import Cooccurrence
from base import BaseMapper
import numpy as np

class ConservativeDirectMapper(BaseMapper):
    """
    Maps left label a to right label b if b is the only one cooccurring with a.
    """
    def __init__(self):
        super(ConservativeDirectMapper, self).__init__()
    
    def _associate(self, A, B):
        
        # Cooccurrence matrix
        matrix = Cooccurrence(A, B)
        
        pairs = matrix.argmax(axis=1)
        pairs = {a : b for a, b in pairs.iteritems() 
                       if np.count_nonzero(matrix[a, :].M) == 1}
        
        # Reverse dict and group alabels by argmax
        sriap = {}
        for a, b in pairs.iteritems():
            if b not in sriap:
                sriap[b] = set([])
            sriap[b].add(a)
        
        M = ManyToOneMapping(A.modality, B.modality)
        
        for b, a_s in sriap.iteritems():
            M += (a_s, [b])
        alabels, blabels = matrix.labels
        for a in set(alabels)-M.left_set:
            M += ([a], None)
        for b in set(blabels)-M.right_set:
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
    cost : type
        This parameter controls how function K is computed.
        Defaults to :class:`pyannote.base.matrix.Cooccurrence`, 
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
    pyannote.base.matrix.Cooccurrence, pyannote.base.matrix.CoTFIDF, pyannote.base.matrix
    
    """
    def __init__(self, cost=None):
        super(ArgMaxMapper, self).__init__()
        if cost is None:
            self.__cost = Cooccurrence
        else:
            self.__cost = cost
    
    def _associate(self, A, B):
        
        # Cooccurrence matrix
        matrix = self.__cost(A, B)
        
        # argmax
        pairs = matrix.argmax(axis=1)
        pairs = {a : b for a, b in pairs.iteritems() if matrix[a, b] > 0}
        
        # Reverse dict and group alabels by argmax
        sriap = {}
        for a, b in pairs.iteritems():
            if b not in sriap:
                sriap[b] = set([])
            sriap[b].add(a)
        
        M = ManyToOneMapping(A.modality, B.modality)
        
        for b, a_s in sriap.iteritems():
            M += (a_s, [b])
        alabels, blabels = matrix.labels
        for a in set(alabels)-M.left_set:
            M += ([a], None)
        for b in set(blabels)-M.right_set:
            M += (None, [b])
        
        return M

if __name__ == "__main__":
    import doctest
    doctest.testmod()
