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

import networkx as nx
from pyannote.algorithm.clustering.base import MatrixIMx
from pyannote.algorithm.util.modularity import Modularity
from pyannote.algorithm.clustering.cmx.base import BaseConstraintMixin

class IncreaseModularityCMx(BaseConstraintMixin):
    
    def cmx_setup(self, edge_threshold=0.5, **kwargs):
        if not isinstance(self, MatrixIMx):
            raise ValueError('IncreaseModularityCMx requires MatrixIMx.')
        self.cmx_edge_threshold = edge_threshold
    
    def cmx_init(self):
        g = nx.DiGraph()
        for i, j, s in self.imx_matrix.iter_pairs(data=True):
            if s < self.cmx_edge_threshold:
                continue
            g.add_edge(i, j, weight=1)
        self.cmx_modularity = Modularity(g, weight='weight')
        self.cmx_partition = {i:i for i in self.imx_matrix.iter_ilabels()}
        self.cmx_q = [self.cmx_modularity(self.cmx_partition)]
        
    def cmx_update(self, new_label, merged_labels):
        for label in merged_labels:
            self.cmx_partition[label] = new_label
        self.cmx_q.append(self.cmx_modularity(self.cmx_partition))
    
    def cmx_meet(self, labels):
        partition = dict(self.cmx_partition)
        for label in labels:
            partition[label] = labels[0]
        q = self.cmx_modularity(partition)
        return q > self.cmx_q[-1]

if __name__ == "__main__":
    import doctest
    doctest.testmod()
