#!/usr/bin/env python
# encoding: utf-8

from pyannote.algorithm.clustering.optimization.base import ILPClustering
from pyannote.algorithm.clustering.model.gaussian import BICMMx

class BICILP(ILPClustering, BICMMx):
    def __init__(self, alpha=1e-4, penalty_coef=3.5):
        super(BICILP, self).__init__(alpha=alpha, penalty_coef=penalty_coef)
        
