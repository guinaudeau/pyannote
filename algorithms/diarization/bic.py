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
from base import DiarizationGraph
from ..helper.bic import Gaussian

BIC_CLUSTERING_GAUSSIAN = '__gaussian__'

class BICClustering(DiarizationGraph):
    
    def __init__(self, penalty=7.):
        super(BICClustering, self).__init__()
        self.__penalty = penalty
    
    def __call__(self, annotation, feature=None):
        self.__feature = feature
        super(BICClustering, self).__call__(annotation)
        
    def __get_feature(self): 
        return self.__feature
    feature = property(fget=__get_feature, \
                         fset=None, \
                         fdel=None, \
                         doc="Feature.")
    
    def __get_penalty(self): 
        return self.__penalty
    penalty = property(fget=__get_penalty, \
                         fset=None, \
                         fdel=None, \
                         doc="BIC penalty coefficient.")
    
    # ================================================================== #
    
    def get_base_node(self, segment, track):
        a, attr = super(BICClustering, self).get_base_node(segment, track) 
        g = Gaussian(penalty=self.penalty)
        if self.feature is not None:
            x = self.feature(segment)
        else:
            x = self.annotation[segment, track]
        g.fit(x)
        attr[BIC_CLUSTERING_GAUSSIAN] = g
        return a, attr
    
    # ------------------------------------------------------------------ #

    def get_nodes_distance(self, a, b):
        d = self.node[a][BIC_CLUSTERING_GAUSSIAN] - \
            self.node[b][BIC_CLUSTERING_GAUSSIAN]
        if d > 0:
            return np.inf
        else:
            return d

    # ------------------------------------------------------------------ #
    
    def get_new_node(self, a, b):
        ab, attr = super(BICClustering, self).get_new_node(a, b)
        g = self.node[a][BIC_CLUSTERING_GAUSSIAN] & \
            self.node[b][BIC_CLUSTERING_GAUSSIAN]
        attr[BIC_CLUSTERING_GAUSSIAN] = g
        return ab, attr
    
    # ================================================================== #
    