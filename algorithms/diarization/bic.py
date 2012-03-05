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
from ..helper import Gaussian

class BICClusteringGraph(DiarizationGraph):
    
    def __init__(self, annotation, feature, penalty=7.):
        super(BICClusteringGraph, self).__init__(annotation)
        self.__penalty = penalty
        self.__feature = feature
    
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
        a, attr = super(BICClusteringGraph, self).get_base_node(segment, track) 
        g = Gaussian(penalty=self.penalty)
        g.fit(self.feature(segment))
        attr['gaussian'] = g
        return a, attr
    
    # ------------------------------------------------------------------ #

    def get_nodes_distance(self, a, b):
        d = self.node[a]['gaussian'] - self.node[b]['gaussian']
        if d > 0:
            return np.inf
        else:
            return d
    
    # ================================================================== #
    
    def get_new_node(self, a, b):
        ab, attr = super(BICClusteringGraph, self).get_new_node(a, b)
        g = self.node[a]['gaussian'] & self.node[b]['gaussian']
        attr['gaussian'] = g
        return ab, attr
    
    # ================================================================== #
    