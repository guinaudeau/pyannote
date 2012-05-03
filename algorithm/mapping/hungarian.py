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
from pyannote.base.comatrix import Confusion

class HungarianMapper(BaseMapper):
    """Label mapper based on the Hungarian algorithm
    
    Given two annotations of the same document, the Hungarian algorithm aims
    at solving the following equations:
    
    
    
    
    See [1]_ 
    
    
    Parameters
    ----------
    confusion : Confusion class or sub-class
        Defaults to Confusion.
    force : bool
        force mapping even for labels with zero confusion
        Defaults to False.
    
    Returns
    -------
    mapper : HungarianMapper
    
    Examples
    --------
    
        >>> mapper = HungarianMapper()
        >>> A = Annotation(multitrack=False, modality="speaker")
        >>> A[]
        >>> B = Annotation(multitrack=True, modality="face")
        >>> speaker_face = mapper(A, B)
        
        >>> print speaker_face('Bernard')
        'Bernard'
    
    References
    ----------
    [1] "Hungarian algorithm", http://en.wikipedia.org/wiki/Hungarian_algorithm
    [2] J. Poignant, H. Bredin et al., "Unsupervised Speaker Identification
    using Overlaid Texts in TV Broadcast", submitted to Interspeech 2012.
    
    """
    def __init__(self, confusion=None, force=False):
        super(HungarianMapper, self).__init__()
        self.__force = force
        self.__munkres = Munkres()
        if confusion is None:
            self.__confusion = Confusion
        else:
            self.__confusion = confusion
    
    def __get_munkres(self): 
        return self.__munkres
    munkres = property(fget=__get_munkres, \
                     fset=None, \
                     fdel=None, \
                     doc="Munkres algorithm.")

    def __get_confusion(self): 
        return self.__confusion
    confusion = property(fget=__get_confusion, \
                     fset=None, \
                     fdel=None, \
                     doc="Confusion.")
    
    def __get_force(self): 
        return self.__force
    force = property(fget=__get_force, \
                     fset=None, \
                     fdel=None, \
                     doc="Force mapping?")
    
    def associate(self, A, B):
        
        # Confusion matrix
        matrix = self.confusion(A, B)
        M = OneToOneMapping(A.modality, B.modality)
        
        # Shape and labels
        Na, Nb = matrix.shape
        alabels, blabels = matrix.labels

        # Cost matrix
        N = max(Nb, Na)
        C = np.zeros((N, N))
        C[:Nb, :Na] = (np.max(matrix.M) - matrix.M).T
    
        # Optimal one-to-one mapping
        mapping = self.munkres.compute(C)
    
        for b, a in mapping:
            if (b < Nb) and (a < Na):
                if self.force or (matrix[alabels[a], blabels[b]] > 0):
                    M += ([alabels[a]], [blabels[b]])
    
        # A --> NoMatch
        for alabel in set(alabels)-M.left_set:
            M += ([alabel], None)
    
        # NoMatch <-- B
        for blabel in set(blabels)-M.right_set:
            M += (None, [blabel])
        
        return M
        
if __name__ == "__main__":
    import doctest
    doctest.testmod()

