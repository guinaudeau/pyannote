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
from pyannote.base.association import OneToOneMapping, Mapping, NoMatch
from pyannote.base.comatrix import Confusion
from base import BaseAssociation

class Hungarian(BaseAssociation):
    """
    Hungarian algorithm based on co-occurrence duration.
    
    Finds the best one-to-one mapping between A and B identifiers that,
    when A is translated by this mapping, minimizes the total duration of 
    segments where A and B disagree.
    
    In other words, mapping minimizes the following:
    pyannote.metrics.ier(A % mapping, B, detailed=True)['confusion']
    
    See http://en.wikipedia.org/wiki/Hungarian_algorithm
    
    :param normalize: when True, Hungarian algorithm is applied on normalized
                      confusion matrix.
    :type normalize: boolean
    
    :param init: when provided, Hungarian algorithm is applied within each
                 many-to-many groups.
    :type init: Mapping
    
    :param force: when True, force mapping even for identifiers with zero confusion
    :type force: boolean
    
    """
    def __init__(self, normalize=False, force=False):
        super(Hungarian, self).__init__()
        self.__normalize = normalize
        self.__force = force
        self.__munkres = Munkres()
    
    def __get_normalize(self): 
        return self.__normalize
    normalize = property(fget=__get_normalize, \
                     fset=None, \
                     fdel=None, \
                     doc="Normalize confusion matrix?")

    def __get_force(self): 
        return self.__force
    force = property(fget=__get_force, \
                     fset=None, \
                     fdel=None, \
                     doc="Force mapping?")
    
    def associate(self, A=None, B=None, precomputed=None):
        
        if precomputed is None:
            # Confusion matrix
            matrix = Confusion(B, A, normalize=self.normalize)
            M = OneToOneMapping(A.modality, B.modality)
        else:
            matrix = precomputed.T.copy()
            M = OneToOneMapping('A', 'B')
        
        # Shape and labels
        Nb, Na = matrix.shape
        blabels, alabels = matrix.labels

        if Na < 1:
            for blabel in blabels:
                M += (None, [blabel])
                return M
        if Nb < 1:
            for alabel in alabels:
                M += ([alabel], None)
                return M
    
        # Cost matrix
        N = max(Nb, Na)
        C = np.zeros((N, N))
        C[:Nb, :Na] = np.max(matrix.M) - matrix.M
    
        # Optimal one-to-one mapping
        mapping = self.__munkres.compute(C)
    
        for b, a in mapping:
            if (b < Nb) and (a < Na):
                if self.force or (matrix[blabels[b], alabels[a]] > 0):
                    M += ([alabels[a]], [blabels[b]])
    
        # A --> NoMatch
        for alabel in set(alabels)-M.first_set:
            M += ([alabel], None)
    
        # NoMatch <-- B
        for blabel in set(blabels)-M.second_set:
            M += (None, [blabel])
        
        return M
