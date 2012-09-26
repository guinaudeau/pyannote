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

from pyannote.base.segment import SlidingWindow
from pyannote import Timeline
from pyannote import LabelMatrix
import networkx as nx

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

class AnnotationGraphGenerator(object):
    """
    Parameters
    ----------
    same : boolean, optional
        If True, tracks with same label are connected 
        with a p=1 probability edge.
    
    diff : boolean, optional
        If True, tracks with different labels are connected
        with a p=0 probability edge.
    
    cooccurring : boolean, optional
        If True, cooccurring tracks are connected with a p=0 probability edge.
    
    """
    def __init__(self, same=False, diff=False, cooccurring=False):
        super(AnnotationGraphGenerator, self).__init__()
        self.same = same
        self.diff = diff
        self.cooccurring = cooccurring
    
    def generate(self, annotation, init=None):
        
        if init is None:
            g = nx.Graph()
        else:
            g = init
        
        # Annotation uri & modality are shared by all tracks 
        uri = annotation.video
        modality = annotation.modality
        # List of labels
        labels = annotation.labels()
    
        # {label: list of tracks with this label} dictionary 
        same_label = {label: [] for label in labels}
        
        for segment, track, label in annotation.iterlabels():
            # Add one node per track to the graph
            node = TrackNode(uri, modality, segment, track)
            g.add_node(node, label=label)
            # Keep track of list of tracks per label
            same_label[label].append(node)
    
        # Add 'same label' edges if requested
        # (it is basically an edge with attribute 'probability=1')
        if self.same:
            for label in labels:
                for n, node in enumerate(same_label[label]):
                    for other_node in same_label[label][n+1:]:
                        g.add_edge(node, other_node, probability=1)
    
        # Add 'diff label' edges if requested
        # (it is basically an edge with attribute 'probability=0')
        if self.diff:
            for l, label in enumerate(labels):
                for node in same_label[label]:
                    for other_label in labels[l+1:]:
                        for other_node in same_label[other_label]:
                            g.add_edge(node, other_node, probability=0)
        
        # Add 'cooccurring track' edges if requested
        if self.cooccurring:
            for S, T, L in annotation.iterlabels():
                N = TrackNode(uri, modality, S, T)
                ann = annotation(S, mode='loose')
                for s, t, l in ann.iterlabels():
                    if s != S or t != T:
                        n = TrackNode(uri, modality, s, t) 
                        g.add_edge(N, n, probability=0)
        
        return g


import networkx as nx
from pyannote.algorithm.clustering.model.base import BaseModelMixin
from pyannote.base.matrix import LabelMatrix, Cooccurrence
import numpy as np
import scipy
import scipy.stats
import scipy.optimize

class SimilarityGraphGenerator(object):
    
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
    
    def __init__(self, **kwargs):
        super(SimilarityGraphGenerator, self).__init__()
        
        # setup model
        MMx = self.getMx(BaseModelMixin)
        if len(MMx) == 0:
            raise ValueError('Missing model mixin (MMx).')
        elif len(MMx) > 1:
            raise ValueError('Too many model mixins (MMx): %s' % MMx)
        self.mmx_setup(**kwargs)
        
    
    def _similarity_matrix(self, iannotation, feature):
        return self.mmx_similarity_matrix(iannotation.labels(),
                                          annotation=iannotation,
                                          feature=feature)
    
    def _groundtruth_matrix(self, iannotation, oannotation):
        
        # groundtruth matrix
        ilabels = iannotation.labels()
        G = LabelMatrix(ilabels, ilabels, dtype=int, default=-1)
        
        # cooccurrence matrix
        C = Cooccurrence(iannotation, oannotation)
        
        # coocurrence graph
        # (add an edge if cooccurrence duration is higher than zero)
        g = nx.Graph()
        for I, O, d in C:
            i = ('i', I)
            o = ('o', O)
            g.add_node(i)
            if d > 0:
                g.add_edge(i, o)
        
        # remove i-orphans
        # (i-label that have no cooccurring o-label)
        orphans = [node for node, degree in g.degree_iter() if degree == 0]
        g.remove_nodes_from(orphans)
        
        # get negative pairs from connected components
        cc = nx.connected_components(g)
        for c, component in enumerate(cc):
            for other_component in cc[c+1:]:
                for status, i in component:
                    if status != 'i':
                        continue
                    for other_status, other_i in other_component:
                        if other_status != 'i':
                            continue
                        G[i, other_i] = 0
                        G[other_i, i] = 0
        
        # remove ambiguous i-labels
        # (i-labels that have more than one cooccurring o-label)
        ambiguous = [node for node, degree in g.degree_iter() if degree > 1
                                                             and node[0] == 'i']
        g.remove_nodes_from(ambiguous)
        
        # get positive pairs from connected components
        cc = nx.connected_components(g)
        for component in cc:
            for n, (status, i) in enumerate(component):
                if status != 'i':
                    continue
                for other_status, other_i in component[n+1:]:
                    if other_status != 'i':
                        continue
                    G[i, other_i] = 1
                    G[other_i, i] = 1
        
        # get negative pairs from connected components
        cc = nx.connected_components(g)
        for c, component in enumerate(cc):
            for other_component in cc[c+1:]:
                for status, i in component:
                    if status != 'i':
                        continue
                    for other_status, other_i in other_component:
                        if other_status != 'i':
                            continue
                        G[i, other_i] = 0
                        G[other_i, i] = 0
        
        return G.M
    
    def fit(self, annotations):
        """
        
        Parameters
        ----------
        annotations : (iannotation, feature, oannotation) iterator
            `iannotation` is the input annotation
            `oannotation` is the expected output annotation
            `feature` contains feature extracted from the corresponding resource
        
        """
        
        S = np.empty((0,1))
        G = np.empty((0,1))
        for iannotation, feature, oannotation in annotations:
            # get label similarity matrix
            s = self._similarity_matrix(iannotation, feature)
            S = np.append(S, s)
            # get label groundtruth matrix
            g = self._groundtruth_matrix(iannotation, oannotation)
            G = np.append(G, g)
        
        # positive/negative scores
        self.P = S[np.where(G==1)]
        self.N = S[np.where(G==0)]
        
        P = self.P
        N = self.N
        
        m = np.mean(P)
        s = np.std(P)
        n = scipy.stats.norm(m, s)
        num_bins = 50
        bins = n.ppf(np.arange(0, 1+1./num_bins, 1./num_bins))
        
        Py, _ = scipy.histogram(P, bins, density=True)
        Ny, _ = scipy.histogram(N, bins, density=True)
        
        X = .5*(bins[:-1]+bins[1:])
        prior = 1. * len(N) / len(P)
        Y = 1. / (1 + prior * Ny / Py)
        
        focus = np.isfinite(X) & np.isfinite(Y) & (X > m-.5*s) & (X < m+.5*s)
        x = X[focus]
        y = Y[focus]
        
        def logistic(x, B, Q, M, v):
            y = 1. / (1. + Q * np.exp(-B*(x-M)))**(1./v)
            return y
        
        popt, _ = scipy.optimize.curve_fit(logistic, x, y, p0=(1., 1., m, 1.))
        
        # t = np.arange(m-3*s, m+3*s, 100)
        # plt.plot(X, Y, 'b.', label='data')
        # plt.plot(t, logistic(t, *popt), 'r', label='fit')
        # plt.legend()
        
        self.popt = popt
        
        return self
    
    def generate(self, iannotation, feature, init=None):
        
        if init is None:
            g = nx.Graph()
        else:
            g = init
        
        uri = iannotation.video
        modality = iannotation.modality
        
        labels = iannotation.labels()
        l2i = {label: l for l, label in enumerate(labels)}
        
        M = self._similarity_matrix(iannotation, feature)
        
        def logistic(x, B, Q, M, v):
            y = 1. / (1. + Q * np.exp(-B*(x-M)))**(1./v)
            return y
        
        M = logistic(M, *(self.popt))

        for S, T, L in iannotation.iterlabels():
            node = TrackNode(uri, modality, S, T)
            g.add_node(node, label=L)
            for s, t, l in iannotation.iterlabels():
                other_node = TrackNode(uri, modality, s, t)
                if l == L:
                    probability = 1
                else:
                    probability = M[l2i[L], l2i[l]]
                g.add_edge(node, other_node, probability=probability)
        
        return g
        
class CoOccurrenceGraphGenerator(object):
    """Generate cross-modal probability graph
    
    Parameters
    ----------
    duration : float, optional
    
    """
    def __init__(self, duration=1.):
        super(CoOccurrenceGraphGenerator, self).__init__()
        self.duration = duration
    
    def _subtracks(self, A, B):
        
        timeline = (A._timeline + B._timeline).segmentation()
        timeline = Timeline([segment for segment in timeline
                             if segment.duration > self.duration
                            and A._timeline.covers(segment, mode='strict')
                            and B._timeline.covers(segment, mode='strict')],
                             video=A.video)
        
        # extent = A._timeline.extent() | B._timeline.extent()
        # window = SlidingWindow(duration=self.duration, step=self.duration,
        #                        start=extent.start, end=extent.end,
        #                        end_mode='strict')
        # timeline = Timeline([segment for segment in window 
        #                      if A._timeline.covers(segment, mode='strict')
        #                     and B._timeline.covers(segment, mode='strict')],
        #                     video=A.video)
        
        a = A >> timeline
        b = B >> timeline
        return a, b, timeline
        
    def fit(self, annotations):
        """
        
        Parameters
        ----------
        annotations : (annotation, annotation) iterator
        
        """
        
        accumulated_N = LabelMatrix(dtype=int, default=0)
        accumulated_n = LabelMatrix(dtype=int, default=0)
        
        for A, B in annotations:
            
            a, b, timeline = self._subtracks(A, B)
            
            for segment in timeline:
                
                lA = a.get_labels(segment)
                lB = b.get_labels(segment)
                
                nA = len(lA)
                nB = len(lB)
                n = len(lA & lB)
                N = nA * nB
                
                try:
                    accumulated_N[nA, nB] = accumulated_N[nA, nB] + N
                    accumulated_n[nA, nB] = accumulated_n[nA, nB] + n
                except Exception, e:
                    accumulated_N[nA, nB] = N
                    accumulated_n[nA, nB] = n
            
        self.P = LabelMatrix(dtype=float, default=-np.inf)
        for nA, nB, N in accumulated_N:
            if N == 0:
                continue
            self.P[nA, nB] = 1. * accumulated_n[nA, nB] / N
        
        return self
    
    def generate(self, A, B, init=None):
        
        if init is None:
            g = nx.Graph()
        else:
            g = init
        
        # URI is shared by both annotations
        uri = A.video
        # 
        modalityA = A.modality
        modalityB = B.modality
            
        a, b, timeline = self._subtracks(A, B)
        
        # Cross-modality edges
        for segment in timeline:
            
            nA = len(a.get_labels(segment))
            nB = len(b.get_labels(segment))
            
            if self.P[nA, nB] <= 0.:
                continue
                
            for tA, lA in a[segment, :].iteritems():
                nodeA = TrackNode(uri, modalityA, segment, tA)
                g.add_node(nodeA, label=lA)
                for tB, lB in b[segment, :].iteritems():
                    nodeB = TrackNode(uri, modalityB, segment, tB)
                    g.add_node(nodeB, label=lB)
                    g.add_edge(nodeA, nodeB, probability=self.P[nA, nB])
        
        # Sub-tracks edges
        g = self._add_subtracks_edges(A, a, g)
        g = self._add_subtracks_edges(B, b, g)
            
        return g

    def _add_subtracks_edges(self, A, a, g):
        """Add p=1 probabilities between a track and its subtracks"""
        
        # annotation & sub-annotation must share the same URI/modality
        uri = A.video
        modality = A.modality
        
        # for each track in annotation
        for S, T, L in A.iterlabels():
            # create the corresponding track ndoe
            N = TrackNode(uri, modality, S, T)
            g.add_node(N, label=L)
            
            # for each sub-track in sub-annotation 
            # (ie. included in original track segment & with same label)
            for s, t, l in a(S, mode='strict').iterlabels():
                if L != l:
                    continue
                # create the corresponding sub-track node
                n = TrackNode(uri, modality, s, t)
                # add a p=1 probability edge
                g.add_edge(N, n, probability=1.)
        
        # return updated graph
        return g


import matplotlib
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection
import pylab


def draw_repere_graph(g):
    
    pos = nx.spring_layout(g, weight='probability')
    
    # one color per modality
    modalities = set([node.modality for node in g])
    node_colors = ['orange', 'purple', 'blue', 'yellow']
    node_color = {modality: node_colors[m] 
                  for m, modality in enumerate(modalities)}
    
    # edges are black, 10px * p
    any_edges = {(e,f): 1.*g[e][f]['probability'] 
                 for (e,f) in g.edges() 
                 if g[e][f]['probability'] not in [0, 1]}
    
    # p=0 probability edges are red, 10px
    diff_edges = [(e,f) for (e,f) in g.edges() if g[e][f]['probability'] == 0]
    
    # p=1 probability edges are green, 10px
    same_edges = [(e,f) for (e,f) in g.edges() if g[e][f]['probability'] == 1]
    
    for edge, probability in any_edges.iteritems():
        nx.draw_networkx_edges(g, pos, edgelist=[edge], width=2, edge_color='k',
                               style='solid', alpha=probability**10,
                               edge_cmap=None, edge_vmin=None, edge_vmax=None,
                               ax=None, arrows=True, label=None)
    
    nx.draw_networkx_edges(g, pos, edgelist=diff_edges, width=1,
                           edge_color='r', style='solid', alpha=0.5,
                           edge_cmap=None, edge_vmin=None, edge_vmax=None,
                           ax=None, arrows=True, label=None)
    
    nx.draw_networkx_edges(g, pos, edgelist=same_edges, width=1,
                           edge_color='g', style='solid', alpha=1,
                           edge_cmap=None, edge_vmin=None, edge_vmax=None,
                           ax=None, arrows=True, label=None)
    
    nx.draw_networkx_nodes(g, pos, nodelist=None, 
                           node_size=[10*node.segment.duration for node in g], 
                           node_color=[node_color[node.modality] for node in g],
                           node_shape='o', alpha=1.0, cmap=None, 
                           vmin=None, vmax=None, ax=None, 
                           linewidths=None, label=None)

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
        pos = nx.spring_layout(g, weight='probability')
    
    if layout == 'timeline':
        
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
                           edge_color='r', style='solid', alpha=0.5,
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
                          reverse=True)
    
    for node in sorted_nodes:
        x, y = pos[node]
        r = .5 * node.segment.duration / extent.duration
        color = colors[node.modality]
        circ = pylab.Circle((x,y), radius=r, facecolor=color, edgecolor='black')
        ax=pylab.gca()
        ax.add_patch(circ)
    

def graph2annotation(g):
    """
    Convert sparsely-connected graph to annotations
    
    Returns
    -------
    annotations : dict
        Dictionary of dictionaries of annotations
        {uri: {modality: annotation}}
    
    """
    annotation = {}
    for c, cc in enumerate(nx.connected_components()):
        for n, node in cc:
            uri = node.uri
            modality = node.modality
            if uri not in annotation:
                annotation[uri] = {}
            if modality not in annotation[uri]:
                annotation[uri][modality] = pyannote.Annotation(video=uri,
                                                   modality=modality)
            annotation[uri][modality][node.segment, node.track] = c
    
    for uri in annotation:
        for modality in annotation[uri]:
            annotation[uri][modality] = annotation[uri][modality].smooth()
    
    return annotation