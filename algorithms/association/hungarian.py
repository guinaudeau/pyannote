#!/usr/bin/env python
# encoding: utf-8

import numpy as np
from munkres import Munkres
from pyannote.base.association import OneToOneMapping, Mapping, NoMatch
from pyannote.base.comatrix import Confusion

class Hungarian(object):
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
    
    def __call__(self, A, B, init=None):
        
        if isinstance(init, Mapping):
            # empty mapping
            M = OneToOneMapping(A.modality, B.modality)
            for alabels, blabels in init:
                a = A(alabels)
                b = B(blabels)
                m = self(a, b, init=None)
                M += m
            return M
    
        # Confusion matrix
        matrix = Confusion(B, A, normalize=self.normalize)
    
        # Shape and labels
        Nb, Na = matrix.shape
        blabels, alabels = matrix.labels

        M = OneToOneMapping(A.modality, B.modality)
    
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
        for alabel in alabels:
            if alabel not in M.first_set:
                M += ([alabel], None)
    
        # NoMatch <-- B
        for blabel in blabels:
            if blabel not in M.second_set:
                M += (None, [blabel])
        
        return M
