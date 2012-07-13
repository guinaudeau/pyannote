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


from pyannote.algorithm.util.modularity import Modularity
from pyannote.algorithm.clustering.agglomerative.base import MatrixIMx
from pyannote.algorithm.clustering.agglomerative.stop.base import MaximumSMx
import networkx as nx

class MaximumModularitySMx(MaximumSMx):
    
    def smx_setup(self, edge_threshold=0., **kwargs):
        if not isinstance(self, MatrixIMx):
            raise ValueError('MaximumModularitySMx requires MatrixIMx.')
        self.smx_edge_threshold = edge_threshold
    
    def smx_init(self):
        g = nx.DiGraph()
        for i, j, s in self.imx_matrix:
            g.add_node(i)
            if s < self.smx_edge_threshold:
                continue
            g.add_edge(i, j, weight=1)
        self.smx_Q = Modularity(g, weight='weight')
        self.smx_partition = {i:i for i in self.imx_matrix.iter_ilabels()}
        self.smx_iterations = [self.smx_Q(self.smx_partition)]
        
    def smx_update(self, new_label, merged_labels):
        for label in merged_labels:
            self.smx_partition[label] = new_label
        self.smx_iterations.append(self.smx_Q(self.smx_partition))

if __name__ == "__main__":
    import doctest
    doctest.testmod()
