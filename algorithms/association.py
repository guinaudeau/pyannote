#!/usr/bin/env python
# encoding: utf-8

import numpy as np
from munkres import Munkres

class NoMatch(object):
    """
    
    """
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

def hungarian(hypothesis, reference):
    """
    Hungarian algorithm
    
    Finds the best mapping of hypothesis to reference identifiers (hypothesis.IDs --> reference.IDs)
    based on their confusion matrix.
    
    http://en.wikipedia.org/wiki/Hungarian_algorithm
    """
    
    # Confusion matrix
    M = reference * hypothesis
    
    # Shape and labels
    Nr, Nh = M.shape
    rlabels, hlabels = M.labels
    
    # Cost matrix
    N = max(Nr, Nh)
    C = np.zeros((N, N))
    C[:Nr, :Nh] = np.max(M.M) - M.M
    
    # Optimal mapping
    mapper = Munkres()
    mapping = mapper.compute(C)
    mapping = {hlabels[h]: rlabels[r] for r, h in mapping \
                                      if (r < Nr) and (h < Nh)}
    NoMatch.reset()
    for hlabel in hlabels:
        if hlabel not in mapping:
            mapping[hlabel] = NoMatch()
    
    return mapping
    