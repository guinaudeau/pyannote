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

import pyannote.algorithm.community
from pyannote.base.mapping import Mapping, OneToOneMapping, NoMatch, MElement 
from pyannote.base.comatrix import Confusion, AutoConfusion
from base import BaseMapper

class Louvain(BaseMapper):
    
    def __init__(self, normalize=False, overlap=False):
        super(Louvain, self).__init__()
        self.__normalize = normalize
        self.__overlap = overlap
    
    def __get_normalize(self): 
        return self.__normalize
    normalize = property(fget=__get_normalize, \
                     fset=None, \
                     fdel=None, \
                     doc="Normalize confusion matrix?")

    def __get_overlap(self): 
        return self.__overlap
    overlap = property(fget=__get_overlap, \
                     fset=None, \
                     fdel=None, \
                     doc="Intra-modality overlap?")

    def __partition_to_cluster(self, partition):
        clusters = {}
        for node in partition:
            if partition[node] not in clusters:
                clusters[partition[node]] = []
            clusters[partition[node]].append(node)
        return clusters

    def __autoconfusion_graph(self, A):
    
        # AutoConfusion matrix
        M = AutoConfusion(A, neighborhood=0., normalize=self.normalize)
    
        # Shape and labels
        Na, Na = M.shape
        alabels, alabels = M.labels
    
        G = nx.Graph()
        for i in range(Na):
            alabel_i = alabels[i]
            anode_i = MElement(A.modality, alabel_i)
            G.add_node(anode_i)
            for j in range(i+1, Na):
                alabel_j = alabels[j]
                anode_j = MElement(A.modality, alabel_j)
                if M[alabel_i, alabel_j] > 0.:
                    G.add_edge(anode_i, anode_j)
                    G[anode_i][anode_j]['weight'] = M[alabel_i, alabel_j]
    
        return G
    
    def __confusion_graph(self, A, B):
    
        # Confusion matrix
        M = Confusion(A, B, normalize=self.normalize)
    
        # Shape and labels
        Na, Nb = M.shape
        alabels, blabels = M.labels
    
        # Confusion graph
        G = nx.Graph()
        for a, alabel in enumerate(alabels):
            anode = MElement(A.modality, alabel)
            G.add_node(anode)
            for blabel in blabels:
                bnode = MElement(B.modality, blabel)
                if a < 1:
                    G.add_node(bnode)
                if M[alabel, blabel] > 0.:
                    G.add_edge(anode, bnode)
                    G[anode][bnode]['weight'] = M[alabel, blabel]
    
        if self.overlap:
            Ga = self.__autoconfusion_graph(A)
            G.add_edges_from(Ga.edges(data=True))
        
            Gb = self.__autoconfusion_graph(B)
            G.add_edges_from(Gb.edges(data=True))
        
        return G
    
    def associate(self, A, B):
        
        G = self.__confusion_graph(A, B)
    
        # Community detection
        partition = pyannote.algorithm.community.best_partition(G)
        clusters = self.__partition_to_cluster(partition)
    
        # Many-to-many mapping
        M = Mapping(A.modality, B.modality)
        for cluster in clusters:
            nodes = clusters[cluster]
            key = [node.element for node in nodes \
                   if node.modality == A.modality]
            value = [node.element for node in nodes \
                     if node.modality == B.modality]
            M += (key, value)
    
        return M

if __name__ == "__main__":
    import doctest
    doctest.testmod()
