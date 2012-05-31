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
import networkx as nx

class Modularity(object):
    """
    
    Parameters
    ----------
    graph : :class:`networkx.Graph`
    
    community : dict
    
    
    
    """
    def __init__(self, G, weight='weight'):
        super(Modularity, self).__init__()
        
        # rename nodes to integers (0 to nnodes-1)
        self.__re_node = {node : n for n, node in enumerate(G.nodes())}
        g = nx.convert_node_labels_to_integers(G)
        
        # adjacency matrix
        A = np.array(nx.to_numpy_matrix(g, weight=weight))
        
        # total weight in graph
        m = np.sum(A)
        
        # node degree (total weight of outgoing edges)
        kin = np.sum(A, axis=0)[:, np.newaxis]
        kout = np.sum(A, axis=1)[:, np.newaxis]
        
        # modularity matrix
        self.__modularity = A/m - kout*kin.T/(m*m)
        
    def __call__(self, partition):
        """
        """
        # rename communities to integers (0 to ncommunities-1)
        re_community = {cty:c for c, cty in enumerate(set(partition.values()))}
        communities = [[] for _ in re_community]
        for node, cty in partition.iteritems():
            communities[re_community[cty]].append(self.__re_node[node])
        
        D = np.zeros(self.__modularity.shape, dtype=bool)
        for cty in communities:
            for i, n in enumerate(cty):
                for m in cty[i:]:
                    D[n, m] = True
                    D[m, n] = True
        
        return np.sum(D*self.__modularity)