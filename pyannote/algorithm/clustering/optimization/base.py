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
        
        # # set up objective parameters
        # # eg. alpha in Finkel approach
        self.alpha = alpha
        # self.omx_setup(**kwargs)
    
    def fit(self, inputs, outputs, features):
        """
        
        Parameters
        ----------
        annotations : list of :class:`Annotation`
        features : list of :class:`Feature`
        
        
        """
        self.fit_posterior(inputs, outputs, features)
    
    def transform(self, annotation, feature):
        
        # get label similarity matrix
        S = self._get_X(annotation, feature)
        # make it a posterior probability
        P = self.transform_posterior(S)
        
        # create ILP model (no objective yet)
        N,N = P.shape
        model, x = new_clustering_model(N, "no_name")
        
        # create and set objective
        objective, direction = obj_IOlogP(x, P, self.alpha)
        model.setObjective(objective, direction)
        model.setParam('OutputFlag', False)
        
        # optimize
        clusters = optimize(N, model, x)
        
        # translate each label into its cluster ID
        labels = annotation.labels()
        translation = {}
        for c, cluster in enumerate(clusters):
            for i in cluster:
                translation[labels[i]] = c
        return annotation % translation
        
        # # build new annotation based on this...
        # new_annotation = annotation.empty()
        # for i, (Si, Ti, _) in enumerate(annotation.iterlabels()):
        #     new_annotation[Si, Ti] = translation[i]
        # 
        # return new_annotation
        