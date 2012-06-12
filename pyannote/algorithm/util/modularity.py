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
from pyannote.base.matrix import LabelMatrix

class Modularity(object):
    """
    Modularity
    
    Parameters
    ----------
    G : networkx.Graph or networkx.DiGraph
        Graph on which modularity is computed.
    weight : str, optional
        
        Defaults to 'weight'
    
    """
    def __init__(self, G, weight='weight'):
        super(Modularity, self).__init__()
        
        # adjacency matrix
        A = LabelMatrix.from_networkx_graph(G, weight=weight)
        
        # total weights in graph
        m = np.sum(A.M)
        
        # node degree (total weight of {in|out}going edges)
        kin = np.sum(A.M, axis=0)[:, np.newaxis]
        kout = np.sum(A.M, axis=1)[:, np.newaxis]
        
        # modularity matrix
        A.M = A.M/m - kout*kin.T/(m*m)
        self.Q = A
    
    def __call__(self, partition):
        """Compute modularity
        
        Parameters
        ----------
        partition : dict
            Dictionary with node as keys and communities as values
            
        Returns
        -------
        modularity : float
            Modularity for given `partition`
        
        """
        
        # same partition matrix
        ilabels, jlabels = self.Q.labels
        D = LabelMatrix(ilabels=ilabels, jlabels=jlabels, 
                        dtype=bool, default=False)
        clusters = {}
        for node, k in partition.iteritems():
            if k not in clusters:
                clusters[k] = set([])
            clusters[k].add(node)
        for _, nodes in clusters.iteritems():
            for n in nodes:
                for m in nodes:
                    D[n, m] = True
        
        # modularity
        return np.sum(D.M * self.Q.M)
    
    # def graph_cut(self):
    #     w, V = np.linalg.eig(self.Q.M)
    #     v = V[:, np.argmax(w)]
    #     return {node: 0 if v[n] < 0 else 1 
    #             for n, node in enumerate(self.Q.iter_ilabels())}
    