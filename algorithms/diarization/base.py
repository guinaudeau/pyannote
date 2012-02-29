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
from pyannote.base.annotation import TrackAnnotation
from pyannote.base.comatrix import CoMatrix

DIARIZATION_DISTANCE = '__distance__'

class DiarizationGraph(nx.Graph):
    
    def __init__(self, annotation):
        
        super(DiarizationGraph, self).__init__()
        self.__annotation = annotation
        self.__initialize()
    
    # ================================================================== #
    
    def __get_annotation(self): 
        return self.__annotation
    annotation = property(fget=__get_annotation, \
                       fset=None, \
                       fdel=None, \
                       doc="Initial annotation")
    
    # ================================================================== #
    
    def get_base_node(self, segment, track):
        A = self.annotation
        a = TrackAnnotation(dict, video=A.video, \
                            modality=A.modality)
        a[segment, track] = {}
        return a, {}   
    
    # ------------------------------------------------------------------ #

    def get_nodes_distance(self, a, b):
        # Nodes that SHOULD NOT be merged have infinity distance        
        raise NotImplementedError('')
    
    # ------------------------------------------------------------------ #

    def __initialize(self):
        
        # add one node per segment/track
        for segment, track in self.annotation.itertracks():
            node, attr = self.get_base_node(segment, track)
            self.add_node(node, **attr)
        
        # add edges with finite distance
        for a in self.nodes_iter():
            for b in self.nodes_iter():
                if (a != b) and \
                   (not self.has_edge(b, a)):
                    d = self.get_nodes_distance(a, b)
                    if d < np.inf:
                        self.add_edge(a, b, **{DIARIZATION_DISTANCE:d})
    
    # ================================================================== #
    
    def __closest(self):
        nodes = self.nodes()
        N = len(nodes)
        m = np.inf * np.ones((N, N))
        for i, a in enumerate(self.nodes()):
            for j, b in enumerate(self.nodes()):
                if i > j and self.has_edge(a, b):
                    m[i, j] = self[a][b][DIARIZATION_DISTANCE]        
        M = CoMatrix(nodes, nodes, m)
        pairs = M.argmin(threshold=np.inf)
        return pairs        
    
    # ------------------------------------------------------------------ #

    def get_new_node(self, a, b):
        ab = a.copy()
        for segment, track, data in b.itertracks(data=True):
            ab[segment, track] = data
        return ab, {}
    
    # ================================================================== #
    
    def diarize(self):
        pairs = self.__closest()
        while(pairs):
            a, b = pairs[0]
            ab, attr = self.get_new_node(a, b)
            self.add_node(ab, **attr)
            self.remove_node(a)
            self.remove_node(b)
            for n in self.nodes_iter():
                if n != ab:
                    d = self.get_nodes_distance(n, ab)
                    if d < np.inf:
                        self.add_edge(ab, n, **{DIARIZATION_DISTANCE:d})
            pairs = self.__closest()
        
    # ================================================================== #


