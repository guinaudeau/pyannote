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

"""

Graphical representations

"""

import numpy as np
import networkx as nx
from pyannote import Timeline
from pyannote.base.matrix import LabelMatrix, Cooccurrence, CoTFIDF
from pyannote.algorithm.clustering.model.base import BaseModelMixin

class IdentityNode(object):
    """Graphical representation of an identity"""
    def __init__(self, identifier):
        super(IdentityNode, self).__init__()
        self.identifier = identifier
    
    def __eq__(self, other):
        return self.identifier == other.identifier
    
    def __hash__(self):
        return hash(self.identifier)
        
    def __str__(self):
        return "[%s]" % (self.identifier)
    
    def __repr__(self):
        return "<IdentityNode %s>" % self.identifier

class LabelNode(object):
    """Graphical representation of a label"""
    def __init__(self, uri, modality, label):
        super(LabelNode, self).__init__()
        self.uri = uri
        self.modality = modality
        self.label = label
    
    def __eq__(self, other):
        return self.uri == other.uri and \
               self.modality == other.modality and \
               self.label == other.label
    
    def __hash__(self):
        return hash(self.uri) + hash(self.label)
    
    def __str__(self):
        return "%s | %s | %s" % (self.uri, self.modality, self.label)
    
    def __repr__(self):
        return "<LabelNode %s>" % self


class TrackNode(object):
    """Graphical representation of a track"""
    def __init__(self, uri, modality, segment, track):
        super(TrackNode, self).__init__()
        self.uri = uri
        self.modality = modality
        self.segment = segment
        self.track = track
    
    def __eq__(self, other):
        return self.uri == other.uri and \
               self.modality == other.modality and \
               self.segment == other.segment and \
               self.track == other.track
    
    def __hash__(self):
        return hash(self.uri) + hash(self.segment)

    def __str__(self):
        return "%s | %s | %s %s" % (self.uri, self.modality, 
                                    self.segment, self.track)
    
    def __repr__(self):
        return "<TrackNode %s>" % self

# class PreComputedSimilarityGraph(object):
#     """
#     Parameters
#     ----------
#     cooccurring : boolean, optional
#         If True, cooccurring tracks are connected with a p=0 probability edge.
#     func : function
#         Similarity-to-probability function
#     
#     """
#     def __init__(self, func=None, cooccurring=False):
#         super(PreComputedSimilarityGraph, self).__init__()
#         self.cooccurring = cooccurring
#         if func is None:
#             self.func = lambda x: x
#         else:
#             self.func = func
#     
#     def __call__(self, annotation, matrix, init=None):
#         
#         if init is None:
#             g = nx.Graph()
#         else:
#             g = init
#         
#         M = matrix.copy()
#         M.M = self.func(M.M)
#         
#         # Annotation uri & modality are shared by all tracks 
#         uri = annotation.video
#         modality = annotation.modality
#         
#         # Double loop on tracks
#         for S, T, L in annotation.iterlabels():
#             
#             # Add track to the graph
#             node = TrackNode(uri, modality, S, T)
#             g.add_node(node, label=L)
#             
#             # Add edges to all other tracks
#             for s, t, l in annotation.iterlabels():
#                 
#                 # No self loop
#                 if s == S and t == T:
#                     continue
#                 
#                 other_node = TrackNode(uri, modality, s, t)
#                 
#                 # Special case for co-occurring tracks
#                 # (eg. two cooccurring faces cannot be from the same person)
#                 if self.cooccurring and s.intersects(S):
#                     probability = 0.
#                 else:
#                     # it might also happen that similarity between labels
#                     # is not available. then only, set probability to None
#                     try:
#                         probability = M[l, L]
#                     except Exception, e:
#                         probability = None
#                 
#                 if probability is not None:
#                     g.add_edge(node, other_node, probability=probability)
#         
#         return g



# TrackLabelGraph contains LabelNode(s) and TrackNode(s) from the same modality
# and probability=1 edges between LabelNode(s) and TrackNode(s)
class TrackLabelGraph(object):
    
    def __init__(self):
        super(TrackLabelGraph, self).__init__()
        
    def __call__(self, annotation):
        
        # initialize empty graph
        G = nx.Graph()
        uri = annotation.video
        modality = annotation.modality
        
        # one node per label
        labelNodes = {label: LabelNode(uri, modality, label) 
                      for label in annotation.labels()}
        for node in labelNodes:
            G.add_node(node)
        
        # one node per track, connected to its label node
        for segment, track, label in annotation.iterlabels():
            trackNode = TrackNode(uri, modality, segment, track)
            G.add_edge(trackNode, labelNodes[label], probability=1.)
        
        return G

class LabelCoreferenceGraph(object):
    def __init__(self):
        super(LabelCoreferenceGraph, self).__init__()

# LabelCooccurrenceGraph contains LabelNode(s) from 2 different modalities
# and probability edges between cooccurring LabelNodes(s)
class LabelCooccurrenceGraph(object):
    
    def __init__(self, P=None, modalityA=None, modalityB=None):
        super(LabelCooccurrenceGraph, self).__init__()
        if P is not None:
            self.P = P
        if modalityA is not None:
            self.modalityA = modalityA
        if modalityB is not None:
            self.modalityB = modalityB
        
    def fit(self, rAiArBiB_iterator):
        """
        
        Parameters
        ----------
        rAiArBiB_iterator :(reference_A, input_A, reference_B, input_B) iterator
        
        """
        
        ok = {}
        total = {}
        
        modalityA = None
        modalityB = None
        
        for RefA, InpA, RefB, InpB in rAiArBiB_iterator:
        
            # make sure annotation are for the same resource
            uri = RefA.video
            if InpA.video != uri or RefB.video != uri or InpB.video != uri:
                raise ValueError('URI mismatch.')
            
            modA = RefA.modality
            if modalityA is None:
                modalityA = modA
            
            modB = RefB.modality
            if modalityB is None:
                modalityB = modB
                
            # make sure all refs are for the same modality
            if modalityA != modA:
                raise ValueError('Modality mismatch (%s vs. %s)' \
                               % (modalityA, modA))
            if modalityB != modB:
                raise ValueError('Modality mismatch (%s vs. %s)' \
                               % (modalityB, modB))
            
            # make sure Ref/Inp are for the same modality
            if InpA.modality != modA:
                raise ValueError('Modality mismatch (%s vs. %s)' \
                                 % (InpA.modality, modA)) 
            if InpB.modality != modB:
                raise ValueError('Modality mismatch (%s vs. %s)' \
                                 % (InpB.modality, modB)) 
            
            # make sure annotations are for 2 different modalities
            if modA == modB:
                raise ValueError('Both annotations share the same modality.')
            
            # auto-cooccurrence matrix in both annotations
            autoCoA = Cooccurrence(InpA, InpA)
            autoCoB = Cooccurrence(InpB, InpB)
            coA = CoTFIDF(RefA, InpA, idf=False).T
            coB = CoTFIDF(RefB, InpB, idf=False).T
            
            for iA in InpA.labels():
                
                # number of auto-cooccurring labels
                N = np.sum(autoCoA[iA, :].M > 0)
                
                # find reference labels with positive cooccurrence
                mapA = {rA: coA[iA, rA] for rA in coA.labels[1] 
                                        if coA[iA, rA] > 0}
                
                # focus on cooccurring other labels
                for iB in InpB(InpA.label_coverage(iA),
                              mode='intersection').labels():
                    
                    # number of auto-cooccurring labels
                    n = np.sum(autoCoB[iB, :].M > 0)
                    
                    # find reference labels with positive cooccurrence
                    mapB = {rB: coB[iB, rB] for rB in coB.labels[1] 
                                            if coB[iB, rB] > 0}
                    
                    if (N, n) not in ok:
                        ok[N, n] = 0.
                        total[N, n] = 0.
                    
                    total[N, n] += 1.
                    for rAB in set(mapA) & set(mapB):
                        ok[N, n] += mapA[rAB] * mapB[rAB]
        
        self.P = {(N,n): ok[N,n] / total[N,n] for (N,n) in ok}
        self.modalityA = modalityA
        self.modalityB = modalityB
        
        return self
    
    def __call__(self, annotation, other_annotation):
        
        G = nx.Graph()
        
        # make sure annotation are for the same resource
        uri = annotation.video
        if other_annotation.video != uri:
            raise ValueError('URI mismatch.')
        
        # make sure modalities are correct
        modality = annotation.modality
        if modality != self.modalityA:
            raise ValueError('Modality mismatch (%s vs. %s)' \
                             % (modality, self.modalityA))
        
        other_modality = other_annotation.modalityB
        if other_modality != self.modalityB:
            raise ValueError('Modality mismatch (%s vs. %s)' \
                             % (other_modality, self.modalityB))
        
        # auto-cooccurrence matrix in both annotations
        cooccurrence = Cooccurrence(annotation, annotation)
        other_cooccurrence = Cooccurrence(other_annotation, other_annotation)
        
        for L in annotation.labels():
            
            # number of auto-cooccurring labels
            N = np.sum(cooccurrence[L, :].M > 0)
            
            node = LabelNode(uri, modality, L)
            
            # focus on cooccurring other labels
            for l in other_annotation(annotation.label_coverage(L),
                                      mode='intersection').labels():
                
                # number of auto-cooccurring labels
                n = np.sum(other_cooccurrence[l, :].M > 0)
                
                if (N, n) not in self.P:
                    continue
                
                other_node = LabelNode(uri, other_modality, l)
                G.add_edge(node, other_node, probability=self.P[N, n])
        
        return G
        
# LabelIdentityGraph contains LabelNode(s) and IdentityNode(s)
# and probability edges between LabelNode(s) and IdentityNode(s)
class LabelIdentityGraph(object):
    def __init__(self):
        super(LabelIdentityGraph, self).__init__()
    
    def __call__(self, annotation):
        
        # label nodes are sharing the same uri/modality
        uri = annotation.video
        modality = annotation.modality
        
        G = nx.Graph()
        
        identityNodes = []
        
        # link each label with its identity node
        for label in annotation.labels():
            labelNode = LabelNode(uri, modality, label)
            identityNode = IdentityNode(label)
            identityNodes.append(identityNode)
            G.add_edge(labelNode, identityNode, probability=1.)
        
        # identity nodes cannot be merged
        for n, node in enumerate(identityNodes):
            for other_node in identityNodes[n+1:]:
                G.add_edge(node, other_node, probability=0.)
        
        return G
        
# LabelSimilarityGraph contains LabelNode(s) from the same modality
# and probability edges between LabelNode(s) 
class LabelSimilarityGraph(object):
    
    def getMx(self, baseMx):
        
        # get all mixins subclass of baseMx
        # but the class itself and the baseMx itself
        cls = self.__class__
        MX =  [Mx for Mx in cls.mro() 
                  if issubclass(Mx, baseMx) and Mx != cls and Mx != baseMx]
        
        # build the class inheritance directed graph {subclass --> class}
        G = nx.DiGraph()
        for m, Mx in enumerate(MX):
            G.add_node(Mx)
            for otherMx in MX[m+1:]:
                if issubclass(Mx, otherMx):
                    G.add_edge(Mx, otherMx)
                elif issubclass(otherMx, Mx):
                    G.add_edge(otherMx, Mx)
        
        # only keep the deeper subclasses in each component
        MX = []
        for components in nx.connected_components(G.to_undirected()):
            g = G.subgraph(components)
            MX.extend([Mx for Mx, degree in g.in_degree_iter() if degree == 0])
        
        return MX
    
    def __init__(self, func=None, cooccurring=True, **kwargs):
        """
        
        Parameters
        ----------
        func : function
            Similarity-to-probability function
        cooccurring : boolean
            If True, cooccurring labels edges are set to 0 probability
        """
        super(LabelSimilarityGraph, self).__init__()
        self.cooccurring = cooccurring
        
        # setup model
        MMx = self.getMx(BaseModelMixin)
        if len(MMx) == 0:
            raise ValueError('Missing model mixin (MMx).')
        elif len(MMx) > 1:
            raise ValueError('Too many model mixins (MMx): %s' % MMx)
        self.mmx_setup(**kwargs)
        
        if func is None:
            self.func = lambda x: x
        else:
            self.func = func
    
    def __call__(self, annotation, feature):
        
        # list of labels in annotation & their number
        labels = annotation.labels()  
        N = len(labels)
        
        # NxN label similarity matrix
        S = self.mmx_similarity_matrix(labels, annotation=annotation,
                                               feature=feature)
        # Label probability matrix
        P = self.func(S)
        
        # Initialize empty graph
        G = nx.Graph()
        uri = annotation.video
        modality = annotation.modality
        
        # Label cooccurrence matrix
        if self.cooccurring:
            K = Cooccurrence(annotation, annotation)
        
        # Complete undirected graph with one LabelNode per label 
        for l, label in enumerate(labels):
            node = LabelNode(uri, modality, label)
            G.add_node(node)
            for L in range(l+1, N):
                other_label = labels[L]
                other_node = LabelNode(uri, modality, other_label)
                # Label-to-label edge is weighted by probability
                # or set to 0. if labels are cooccurring (the same person
                # cannot appear twice at the same time...)
                if self.cooccurring and K[label, other_label] > 0.:
                    p = 0.
                else:
                    p = P[l, L]
                G.add_edge(node, other_node, probability=p)
        
        return G

# class CooccurrenceGraph(object):
#     """Generate cross-modal probability graph
#     
#     Parameters
#     ----------
#     duration : float, optional
#     
#     """
#     def __init__(self, duration=1.):
#         super(CooccurrenceGraph, self).__init__()
#         self.duration = duration
#     
#     def _subtracks(self, A, B):
#         
#         timeline = (A._timeline + B._timeline).segmentation()
#         timeline = Timeline([segment for segment in timeline
#                              if segment.duration > self.duration
#                             and A._timeline.covers(segment, mode='strict')
#                             and B._timeline.covers(segment, mode='strict')],
#                              video=A.video)
#         
#         # extent = A._timeline.extent() | B._timeline.extent()
#         # window = SlidingWindow(duration=self.duration, step=self.duration,
#         #                        start=extent.start, end=extent.end,
#         #                        end_mode='strict')
#         # timeline = Timeline([segment for segment in window 
#         #                      if A._timeline.covers(segment, mode='strict')
#         #                     and B._timeline.covers(segment, mode='strict')],
#         #                     video=A.video)
#         
#         a = A >> timeline
#         b = B >> timeline
#         return a, b, timeline
#         
#     def fit(self, annotations):
#         """
#         
#         Parameters
#         ----------
#         annotations : (annotation, annotation) iterator
#         
#         """
#         
#         accumulated_N = LabelMatrix(dtype=int, default=0)
#         accumulated_n = LabelMatrix(dtype=int, default=0)
#         
#         for A, B in annotations:
#             
#             a, b, timeline = self._subtracks(A, B)
#             
#             for segment in timeline:
#                 
#                 lA = a.get_labels(segment)
#                 lB = b.get_labels(segment)
#                 
#                 nA = len(lA)
#                 nB = len(lB)
#                 n = len(lA & lB)
#                 N = nA * nB
#                 
#                 try:
#                     accumulated_N[nA, nB] = accumulated_N[nA, nB] + N
#                     accumulated_n[nA, nB] = accumulated_n[nA, nB] + n
#                 except Exception, e:
#                     accumulated_N[nA, nB] = N
#                     accumulated_n[nA, nB] = n
#             
#         self.P = LabelMatrix(dtype=float, default=-np.inf)
#         for nA, nB, N in accumulated_N:
#             if N == 0:
#                 continue
#             self.P[nA, nB] = 1. * accumulated_n[nA, nB] / N
#         
#         return self
#     
#     def __call__(self, A, B, init=None):
#         
#         if init is None:
#             g = nx.Graph()
#         else:
#             g = init
#         
#         # URI is shared by both annotations
#         uri = A.video
#         # 
#         modalityA = A.modality
#         modalityB = B.modality
#             
#         a, b, timeline = self._subtracks(A, B)
#         
#         # Cross-modality edges
#         for segment in timeline:
#             
#             nA = len(a.get_labels(segment))
#             nB = len(b.get_labels(segment))
#             
#             if self.P[nA, nB] <= 0.:
#                 continue
#                 
#             for tA, lA in a[segment, :].iteritems():
#                 nodeA = TrackNode(uri, modalityA, segment, tA)
#                 g.add_node(nodeA, label=lA)
#                 for tB, lB in b[segment, :].iteritems():
#                     nodeB = TrackNode(uri, modalityB, segment, tB)
#                     g.add_node(nodeB, label=lB)
#                     g.add_edge(nodeA, nodeB, probability=self.P[nA, nB])
#         
#         # Sub-tracks edges
#         g = self._add_subtracks_edges(A, a, g)
#         g = self._add_subtracks_edges(B, b, g)
#             
#         return g
# 
#     def _add_subtracks_edges(self, A, a, g):
#         """Add p=1 probabilities between a track and its subtracks"""
#         
#         # annotation & sub-annotation must share the same URI/modality
#         uri = A.video
#         modality = A.modality
#         
#         # for each track in annotation
#         for S, T, L in A.iterlabels():
#             # create the corresponding track ndoe
#             N = TrackNode(uri, modality, S, T)
#             g.add_node(N, label=L)
#             
#             # for each sub-track in sub-annotation 
#             # (ie. included in original track segment & with same label)
#             for s, t, l in a(S, mode='strict').iterlabels():
#                 if L != l:
#                     continue
#                 # create the corresponding sub-track node
#                 n = TrackNode(uri, modality, s, t)
#                 # add a p=1 probability edge
#                 g.add_edge(N, n, probability=1.)
#         
#         # return updated graph
#         return g


import pyannote
from matplotlib import pylab
from matplotlib import pyplot

def draw_repere_graph(g, layout='spring'):
    
    nodes = g.nodes()
    modalities = set([node.modality for node in nodes])
    
    extent = pyannote.Segment()
    for node in nodes:
        extent |= node.segment
    
    if layout == 'spring':
        G = g.copy()
        for e, f, d in G.edges(data=True):
            if d['probability'] == 1.:
                G[e][f]['probability'] = 1e4
            # if d['probability'] == 0.:
            #     G[e][f]['probability'] = -1e2                
        pos = nx.spring_layout(G, weight='probability')
    elif layout == 'timeline':
        
        y = {'speaker': 0.8,
             'written': 0.6,
             'head': 0.4,
             'spoken': 0.2}
        
        pos = {}
        for node in nodes:
            x = (node.segment.middle - extent.start) / extent.duration
            pos[node] = (x, y[node.modality])
                     
    # edges are black
    any_edges = {(e,f): 1.*g[e][f]['probability'] 
                 for (e,f) in g.edges() 
                 if g[e][f]['probability'] not in [0, 1]}
    
    # p=0 probability edges are red
    diff_edges = [(e,f) for (e,f) in g.edges() if g[e][f]['probability'] == 0]
    
    # p=1 probability edges are green
    same_edges = [(e,f) for (e,f) in g.edges() if g[e][f]['probability'] == 1]
    
    for edge, probability in any_edges.iteritems():
        nx.draw_networkx_edges(g, pos, edgelist=[edge], width=2, edge_color='k',
                               style='solid', alpha=probability**10,
                               edge_cmap=None, edge_vmin=None, edge_vmax=None,
                               ax=None, arrows=True, label=None)
    
    nx.draw_networkx_edges(g, pos, edgelist=diff_edges, width=1,
                           edge_color='r', style='solid', alpha=0.1,
                           edge_cmap=None, edge_vmin=None, edge_vmax=None,
                           ax=None, arrows=True, label=None)
    
    nx.draw_networkx_edges(g, pos, edgelist=same_edges, width=1,
                           edge_color='g', style='solid', alpha=1,
                           edge_cmap=None, edge_vmin=None, edge_vmax=None,
                           ax=None, arrows=True, label=None)
    
    # one color per modality
    colors = {'speaker': 'purple',
              'written': 'orange',
              'head': 'blue',
              'spoken': 'yellow'}
    
    # draw long segments first (so that they're in the background)
    sorted_nodes = sorted(nodes, 
                          key=lambda node: node.segment.duration,
                          reverse=False)
    
    for node in sorted_nodes:
        x, y = pos[node]
        r = .5 * node.segment.duration / extent.duration
        color = colors[node.modality]
        circ = pylab.Circle((x,y), radius=r, facecolor=color, edgecolor='black')
        ax=pylab.gca()
        ax.add_patch(circ)
    

# def graph2annotation(g):
#     """
#     Convert sparsely-connected graph to annotations
#     
#     Returns
#     -------
#     annotations : dict
#         Dictionary of dictionaries of annotations
#         {uri: {modality: annotation}}
#     
#     """
#     annotation = {}
#     for c, cc in enumerate(nx.connected_components(g)):
#         for n, node in enumerate(cc):
#             uri = node.uri
#             modality = node.modality
#             if uri not in annotation:
#                 annotation[uri] = {}
#             if modality not in annotation[uri]:
#                 annotation[uri][modality] = pyannote.Annotation(video=uri,
#                                                    modality=modality)
#             annotation[uri][modality][node.segment, node.track] = c
#     
#     for uri in annotation:
#         for modality in annotation[uri]:
#             annotation[uri][modality] = annotation[uri][modality].smooth()
#     
#     return annotation