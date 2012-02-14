#!/usr/bin/env python
# encoding: utf-8

import numpy as np
from munkres import Munkres
# from helper import NoMatch

from pyannote.base.association import OneToOneMapping

def hungarian(A, B):
    """
    Hungarian algorithm based on co-occurrence duration.
    
    Finds the best one-to-one mapping between A and B identifiers that,
    when A is translated by this mapping, minimizes the total duration of 
    segments where A and B disagree.
    
    In other words, mapping minimizes the following:
    pyannote.metrics.ier(A % mapping, B, detailed=True)['confusion']
    
    See http://en.wikipedia.org/wiki/Hungarian_algorithm
    """
    
    # Confusion matrix
    M = B * A
    
    # Shape and labels
    Nb, Na = M.shape
    blabels, alabels = M.labels
    
    # Cost matrix
    N = max(Nb, Na)
    C = np.zeros((N, N))
    C[:Nb, :Na] = np.max(M.M) - M.M
    
    # Optimal one-to-one mapping
    mapper = Munkres()
    mapping = mapper.compute(C)
    
    M = OneToOneMapping(A.modality, B.modality)
    for b, a in mapping:
        if (b < Nb) and (a < Na):
            M += ([alabels[a]], [blabels[b]])
    
    # mapping = {alabels[a]: blabels[b] for b, a in mapping \
    #                                   if (b < Nb) and (a < Na)}
    # 
    # # Add a NoMatch mapping to unmatched identifiers
    # NoMatch.reset()
    
    # A --> NoMatch
    for alabel in alabels:
        if alabel not in M.first_set:
            M += ([alabel], None)
    
    # NoMatch <-- B
    for blabel in blabels:
        if blabel not in M.second_set:
            M += (None, [blabel])
    
    return M
