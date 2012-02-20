#!/usr/bin/env python
# encoding: utf-8

import numpy as np
from munkres import Munkres
# from helper import NoMatch

from pyannote.base.association import OneToOneMapping, Mapping, NoMatch
from pyannote.base.comatrix import Confusion

def hungarian(A, B, normalize=False, init=None, force=False):
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
    
    if isinstance(init, Mapping):
        # empty mapping
        M = OneToOneMapping(A.modality, B.modality)
        for alabels, blabels in init:
            alabels = [label for label in alabels if not isinstance(label, NoMatch)]
            blabels = [label for label in blabels if not isinstance(label, NoMatch)]
            a = A(alabels)
            b = B(blabels)
            m = hungarian(a, b, normalize=normalize, init=None)
            for alabel, blabel in m:
                M += (alabel, blabel)
        return M
    
    # Confusion matrix
    matrix = Confusion(B, A, normalize=normalize)
    
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
    mapper = Munkres()
    mapping = mapper.compute(C)
    
    for b, a in mapping:
        if (b < Nb) and (a < Na):
            if force or (matrix[blabels[b], alabels[a]] > 0):
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
