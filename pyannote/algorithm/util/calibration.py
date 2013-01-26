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


from pyannote.base.annotation import Annotation, Scores, Unknown
from pyannote.algorithm.tagging import ArgMaxDirectTagger
import numpy as np
import sc2llr

class IDScoreCalibration(object):
    
    def __init__(self):
        super(IDScoreCalibration, self).__init__()
    
    def _s2llr_mapping(self, X, Y):
        X = np.array(X)
        Y = np.array(Y)
        positive = X[np.where(Y == True)]
        negative = X[np.where(Y == False)]
        return sc2llr.computeLinearMapping(negative, positive)
    
    def _X_Y(self, reference, score):
        """
        
        reference : Annotation
        score : Scores
        
        Returns
        -------
        X : list of scores
            track vs. target scores
        Y : list of boolean
            track vs. target groundtruth
        Xi, Yi :
            same as X,Y but per target
        
        """
        target = score.labels()
        
        X = []
        Xi = {L: [] for L in target}
        Y = []
        Yi = {L: [] for L in target}
        
        for s,t,l in reference.iterlabels():
            
            if isinstance(l, Unknown):
                continue
            
            for L in target:
                v = score[s,t,L]
                X.append(v)
                Y.append(L==l)
                Xi[L].append(v)
                Yi[L].append(L==l)
        
        return X, Y, Xi, Yi
    
    def fit(self, targets, references, scores):
        """
        targets :
        references : func (uri --> Annotation)
        scores : func (uri --> Scores)
        
        `references` and `scores` must contains the same tracks
        """
        
        self.targets = targets
        
        # prior probability for each target
        Pi = {}
        # prior probability for unknown
        Pu = 0.
        
        # score distributions
        X = []
        Y = []
        # per target
        Xi = {}
        Yi = {}
        
        tagger = ArgMaxDirectTagger()
        
        for reference, score in zip(references, scores):
            
            # accumulate target (and unknown) duration
            for L in reference.labels():
                if L in targets:
                    Pi[L] = Pi.get(L, 0) + reference.label_duration(L)
                else:
                    Pu = Pu + reference.label_duration(L)
            
            # accumulate score distribution
            x, y, xi, yi = self._X_Y(reference, score)
            X = X + x
            for i,x in xi.iteritems():
                Xi[i] = Xi.get(i,[]) + x
            Y = Y + y
            for i,y in yi.iteritems():
                Yi[i] = Yi.get(i,[]) + y
        
        # make Pu a probability
        self.Pu = Pu / (Pu + sum([duration for _,duration in Pi.iteritems()]))
        # uniform prior probability for targets
        self.Pk = (1 - self.Pu) / len(targets)
        
        # (target-independent) score to log-likelihood ratio
        self.s2llr = self._s2llr_mapping(X, Y)
        
        return self
    
    
    def _s2p(self, scores):
        """
        Parameters
        ----------
        scores : dict
            target to score dictionary
        
        Returns
        -------
        prob : dict
            target to posterior probability dictionary
        """
        prob = {}
        a, b = self.s2llr
        lr = {i: self.Pk*np.exp(a*s+b) for i,s in scores.iteritems()}
        lr_sum = sum([v for _,v in lr.iteritems()])
        for i, s in scores.iteritems():
            rho = lr[i] / (lr_sum - lr[i] + self.Pu)
            prob[i] = rho / (1+rho)
        return prob
    
    def __call__(self, scores):
        """
        
        Parameters
        ----------
        scores : Scores
        
        Returns
        -------
        probs : Scores
            Scores converted to probabilities
        
        """
        probs = Scores(uri=scores.uri, modality=scores.modality)
        for s, t in scores.itertracks():
            prob = self._s2p(scores.get_track_scores(s,t))
            for target, p in prob.iteritems():
                probs[s,t,target] = p
        return probs
    