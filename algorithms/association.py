#!/usr/bin/env python
# encoding: utf-8

import numpy as np
from munkres import Munkres
import networkx as nx

class NoMatch(object):
    nextID = 0
    
    @classmethod
    def reset(cls):
        cls.nextID = 0
    
    def __init__(self, format='NoMatch%03d'):
        super(NoMatch, self).__init__()
        self.ID = NoMatch.nextID
        self.format = format
        NoMatch.nextID += 1
    
    def __str__(self):
        return self.format % self.ID
    
    def __repr__(self):
        return str(self)

def hungarian(A, B):
    """
    Hungarian algorithm
    
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
    mapping = {alabels[a]: blabels[b] for b, a in mapping \
                                      if (b < Nb) and (a < Na)}
    
    # Add a NoMatch mapping to unmatched identifiers
    NoMatch.reset()
    
    # A --> NoMatch
    for alabel in alabels:
        if alabel not in mapping:
            mapping[alabel] = NoMatch()
    
    # NoMatch <-- B
    mapped = mapping.values()
    for blabel in blabels:
        if blabel not in mapped:
            mapping[NoMatch()] = blabel
    
    return mapping

