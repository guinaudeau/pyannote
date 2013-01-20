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
from matplotlib import pyplot as plt
from pyannote.algorithm.mpg.graph import PROBABILITY, SUBTRACK
from pyannote.algorithm.mpg.node import IdentityNode, LabelNode, TrackNode

def draw_mpg(g, threshold=0.1):
    
    plt.ion()
    
    # remove inodes that have no edge higher than p=0.1
    inodes = [n for n in g 
                if isinstance(n, IdentityNode) 
                and max([g[n][m][PROBABILITY] for m in g.neighbors(n)]) < threshold]
    G = nx.Graph(g)
    G.remove_nodes_from(inodes)
    
    pos = nx.spring_layout(G, weight=PROBABILITY)
    for e,f,d in G.edges_iter(data=True):
        probability = d[PROBABILITY]
        
        # mark 'forbidden' edges with an 'x'
        if probability == 0:
            if isinstance(e, IdentityNode) and isinstance(f, IdentityNode):
                continue
            nx.draw_networkx_edges(G, pos, edgelist=[(e,f)], 
                                           edge_color='r', 
                                           width=1., style='dotted')
            nx.draw_networkx_edge_labels(G, pos, edge_labels={(e,f): 'x'})
        
        # show 'mandatory' edges with a black thick line
        elif probability == 1:
            nx.draw_networkx_edges(G, pos, edgelist=[(e,f)], width=3., 
                                   edge_color='g')
        
        # thickness and transparency of all other edges are 
        # proportional to the probability
        else:
            if probability > threshold:
                nx.draw_networkx_edges(G, pos, edgelist=[(e,f)], 
                                               width=3*probability, 
                                               alpha=probability,
                                               style='dashed')
    
    shapes = {TrackNode: 's', IdentityNode: 'o', LabelNode: 'h'}
    colors = {'speaker': 'r', 'head': 'g', 'written': 'b', 'spoken': 'y'}
    
    for nodeType, node_shape in shapes.iteritems(): 
        nodelist = [n for n in G if isinstance(n, nodeType)]
        if nodeType == IdentityNode:
            node_color = 'w'
            nx.draw_networkx_nodes(G, pos, 
                                   node_size=1000,
                                   nodelist=nodelist,
                                   node_shape=node_shape, 
                                   node_color=node_color)
            nx.draw_networkx_labels(G, pos, font_size=8,
                                    labels={n:n.short() for n in nodelist})
        else:
            for modality, node_color in colors.iteritems():
                nodesublist = [n for n in nodelist 
                                 if n.modality == modality]
                node_size = [50 if G.node[n].get(SUBTRACK, False) else 300 
                             for n in nodesublist]
                nx.draw_networkx_nodes(G, pos, 
                                       node_size=node_size,
                                       nodelist=nodesublist,
                                       node_shape=node_shape,
                                       node_color=node_color)
            if nodeType == TrackNode:
                nx.draw_networkx_labels(G, pos, font_size=8,
                                        labels={n:n.track for n in nodelist})
    
    plt.draw()

from pyannote.algorithm.mpg.graph import AnnotationGraph
def draw_annotation(annotation):
    g = AnnotationGraph()(annotation)
    draw_mpg(g)
    