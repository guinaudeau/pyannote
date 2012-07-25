#!/usr/bin/env python
# encoding: utf-8

import gurobipy as grb
import numpy as np
import networkx as nx
import pyfusion.normalization.bayes


from pyannote.algorithm.clustering.model.base import PosteriorMixin
from pyannote.algorithm.clustering.optimization.gurobi import new_clustering_model, optimize
from pyannote.algorithm.clustering.optimization.objective import obj_IOlogP

class ILPClustering(PosteriorMixin):
    
    def __init__(self, alpha=None, **kwargs):
        super(ILPClustering, self).__init__()
        
        # set up track similarity parameters
        # eg. penalty coefficient for BIC
        self.mmx_setup(**kwargs)
        
        # set up 
        self.alpha = alpha
    
    def fit(self, annotations, features):
        """
        
        Parameters
        ----------
        annotations : list of :class:`Annotation`
        features : list of :class:`Feature`
        
        
        """
        self.fit_posterior(annotations, features)
    
    def transform(self, annotation, feature):
        
        # get tracks similarity & make it a posterior probability P
        S = self._get_X(annotation, feature)
        P = self.transform_posterior(S)
        
        N,N = P.shape
        model, x = new_clustering_model(N, "no_name")
        
        objective, direction = obj_IOlogP(x, P, self.alpha)
        model.setObjective(objective, direction)
        clusters = optimize(N, model, x)
        
        translation = {}
        for c, cluster in enumerate(clusters):
            for i in cluster:
                translation[i] = c
        
        # build new annotation based on this...
        new_annotation = annotation.empty()
        for i, (Si, Ti, _) in enumerate(annotation.iterlabels()):
            new_annotation[Si, Ti] = translation[i]
        
        return new_annotation
        