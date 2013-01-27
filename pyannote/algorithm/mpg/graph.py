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

from pyannote.base.segment import Segment
from pyannote.base.timeline import Timeline
from pyannote.base.annotation import Unknown, Annotation, Scores
from pyannote.base.matrix import Cooccurrence
from pyannote.algorithm.clustering.model.base import BaseModelMixin
from pyannote.base.segment import Segment
from pyannote.base.timeline import Timeline
from pyannote.base.annotation import Unknown, Annotation, Scores
from pyannote.base.matrix import Cooccurrence
from pyannote.algorithm.clustering.model.base import BaseModelMixin
from pyannote.algorithm.mpg.node import IdentityNode, LabelNode, TrackNode
from pandas import DataFrame
import networkx as nx
import numpy as np

PROBABILITY = 'probability'
SUBTRACK = 'subtrack'
COOCCURRING = 'cooccurring'
RANK = 'rank'

class MultimodalProbabilityGraph(nx.Graph):
    
    def __init__(self, **kwargs):
        super(MultimodalProbabilityGraph, self).__init__(**kwargs)
    
    @classmethod
    def merge_prob(cls, old_prob, new_prob):
        
        if new_prob is None:
            return old_prob
        
        if old_prob is None:
            return new_prob
        
        if old_prob in [0,1]:
            if new_prob != old_prob:
                raise ValueError('Prob conflict: old=%g, new=%g' % (old_prob, new_prob))
            return old_prob
        
        return max(old_prob, new_prob)
    
    @classmethod
    def merge_cooc(cls, old_cooc, new_cooc):
        
        if new_cooc is None:
            return old_cooc
        
        if old_cooc is None:
            return new_cooc
        
        if old_cooc != new_cooc:
            raise ValueError('Cooc conflict: old=%g, new=%g' % (old_cooc, new_cooc))
        
        return new_cooc
    
    @classmethod
    def merge_strk(cls, old_strk, new_strk):
        
        if new_strk is None:
            return old_strk
        
        if old_strk is None:
            return new_strk
        
        if old_strk != new_strk:
            raise ValueError('Strk conflict: old=%g, new=%g' % (old_strk, new_strk))
        
        return new_strk
    
    def update_edge(self, node1, node2, 
                       probability=None, 
                       cooccurring=None, 
                       subtrack=None):
        
        if self.has_edge(node1, node2):
            old_attr = dict(self.edge[node1][node2])
            old_prob = old_attr.get(PROBABILITY, None)
            old_cooc = old_attr.get(COOCCURRING, None)
            old_strk = old_attr.get(SUBTRACK, None)
        else:
            old_prob = None
            old_cooc = None
            old_strk = None
        
        new_prob = self.merge_prob(old_prob, probability)
        new_cooc = self.merge_cooc(old_cooc, cooccurring)
        new_strk = self.merge_strk(old_strk, subtrack)
        
        new_attr = {}
        if new_prob is not None:
            new_attr[PROBABILITY] = new_prob
        if new_cooc is not None:
            new_attr[COOCCURRING] = new_cooc
        if new_strk is not None:
            new_attr[SUBTRACK] = new_strk
        
        self.add_edge(node1, node2, **new_attr)
    
    def add(self, other_mpg):
        """Add nodes and edges from other MPG
        """
        
        for node, data in other_mpg.nodes(data=True):
            self.add_node(node, **data)
        
        for e,f,d in other_mpg.edges(data=True):
            self.update_edge(e,f,**d)
    
    def add_track_constraints(self):
        """Add p=0 edges between each intra-modality pair of 
        cooccurring tracks"""
        
        # obtain the list of all modalities in graph
        modalities = set([n.modality for n in self 
                                     if isinstance(n, TrackNode)])
        
        for modality in modalities:
            # obtain the list of tracks for this modality
            # (note that subtracks are not part of this list, 
            # they are hard-linked to their main track anyway)
            tnodes = [n for n in self if isinstance(n, TrackNode) \
                                      and n.modality == modality \
                                      and not self.node[n].get(SUBTRACK, False)]
            
            # loop on each pair of tracks and check for overlapping ones
            for n, node in enumerate(tnodes):
                for other_node in tnodes[n+1:]:
                    # are they overlapping?
                    if node.segment.intersects(other_node.segment):
                        self.update_edge(node, other_node, 
                                         probability=0., cooccurring=True)
    
    def add_identity_constraints(self):
        """Add p=0 edges between each pair of identity nodes
        """
        inodes = [node for node in self if isinstance(node, IdentityNode)]
        for n, node in enumerate(inodes):
            for other_node in inodes[n+1:]:
                self.update_edge(node, other_node, probability=0.)
    
    def propagate_constraints(self):
        """Propagate p=0 and p=1 probabilities edges
        """
        
        # propagated p=1 constraints
        p1 = []
        c = nx.Graph(self)
        c.remove_edges_from([(e,f) for e,f,d in self.edges_iter(data=True)
                                   if d[PROBABILITY] != 1])
        components = nx.connected_components(c)
        for component in components:
            for i,n in enumerate(component):
                for m in component[i+1:]:
                    p1.append((n,m))
        
        # propagated p=0 constraints
        p0 = []
        c = nx.Graph(self)
        c.remove_edges_from([(e,f) for e,f,d in self.edges_iter(data=True)
                                   if d[PROBABILITY] != 0])
        c = nx.blockmodel(c, components, multigraph=True)
        for e,f in c.edges_iter():
            for n in components[e]:
                for m in components[f]:
                    p0.append((n,m))
        
        for n,m in p1:
            self.update_edge(n,m, probability=1.)
        for n,m in p0:
            self.update_edge(n,m, probability=0.)
        
        return self
    
    def get_tracks_by_name(self, modality, name):
        tnodes = [n for n in self if isinstance(n, TrackNode)
                                 and n.track == name
                                 and n.modality == modality]
        return tnodes
    
    def get_tracks_by_time(self, modality, seconds):
        tnodes = [n for n in self if isinstance(n, TrackNode)
                                 and n.segment.start <= seconds
                                 and n.segment.end >= seconds]
        return tnodes
    
    def get_label(self, modality, name):
        lnodes = [n for n in self if isinstance(n, LabelNode)
                                 and n.label == name
                                 and n.modality == modality]
        return lnodes[0]
        
    def get_identity(self, name):
        inodes = [n for n in self if isinstance(n, IdentityNode)
                                 and n.identifier == name]
        return inodes[0]
    
    def _log(self):
        
        # new graph containing nodes from input graph
        log = nx.Graph()
        log.add_nodes_from(self.nodes_iter(data=True))
    
        # convert P to -log P for all input edges
        # don't add the edge when P = 0
        for e,f,d in self.edges_iter(data=True):
            D = dict(d)
            p = d[PROBABILITY]
            if p > 0:
                D[PROBABILITY] = -np.log(p)
                log.add_edge(e,f,D)
        
        return log
    
    
    def shortest_path(self, inode, tnode):
        log = self._log()
        
        # remove all inodes but inode
        inodes = [n for n in log if isinstance(n, IdentityNode)
                                and n != inode]
        log.remove_nodes_from(inodes)
        
        path = nx.shortest_path(log, source=inode, target=tnode, 
                                     weight=PROBABILITY)
        
        P = []
        s = path[0]
        for t in path[1:]:
            p = self[s][t][PROBABILITY]
            print "%.2f %s %s" % (p, s, t)
            P.append(p)
            s = t
        
        return path, P
    
    def complete(self):
        
        # propagate constraints (on a copy) and get -log prob graph
        g = MultimodalProbabilityGraph()
        g.add(self)
        g.propagate_constraints()
        
        log = g._log()
        
        c = MultimodalProbabilityGraph()
        
        # all track nodes of interest
        # ie speaker/head node not subtrack
        tnodes = [(n,d) for n,d in self.nodes_iter(data=True) \
                        if isinstance(n, TrackNode) \
                        and n.modality in ['speaker', 'head'] \
                        and not d.get(SUBTRACK, False)]
        
        # all identity nodes
        inodes = [(n,d) for n,d in self.nodes_iter(data=True) \
                        if isinstance(n, IdentityNode)]
        
        # tnode/tnode shortest path (with forbidden identity nodes)
        _log = nx.Graph(log)
        _log.remove_nodes_from(zip(*inodes)[0])
        # _shortest = nx.shortest_path_length(_log, weight=PROBABILITY)
        # for i, (n, d) in enumerate(tnodes):
        #     c.add_node(n, **d)
        #     for N, D in tnodes[i+1:]:
        #         if g.has_edge(n, N):
        #             data = dict(self[n][N])
        #         else:
        #             data = {PROBABILITY: np.exp(-_shortest[n][N])}
        #         c.update_edge(n, N, **data)
    
        # inode/tnodes shortest path (with forbidden other identity nodes)
        for i, (n, d) in enumerate(inodes):
            c.add_node(n, **d)
            _log = nx.Graph(log)
            _log.remove_nodes_from([m for j,(m,_) in enumerate(inodes) if j != i])
            _shortest = nx.shortest_path_length(_log, source=n, weight=PROBABILITY)
            for N, D in tnodes:
                c.add_node(N, **D)
                if N not in _shortest:
                    continue
                if g.has_edge(n, N):
                    data = dict(g[n][N])
                else:
                    data = {PROBABILITY: np.exp(-_shortest[N])}
                c.update_edge(n, N, **data)
        
        # inode/inode constraint
        c.add_identity_constraints()
        
        return c
    
    def inodes(self):
        return [n for n in self if isinstance(n, IdentityNode)]
    
    def tnodes(self):
        return [n for n in self if isinstance(n, TrackNode)]
    
    def lnodes(self):
        return [n for n in self if isinstance(n, LabelNode)]
    
    def remove_recognition_edges(self, modality):
        inodes = self.inodes()
        tnodes = [n for n in self.tnodes() if n.modality == modality]
        for t in tnodes:
            for i in inodes:
                if self.has_edge(t, i):
                    self.remove_edge(t, i)
    
    def remove_diarization_edges(self, modality):
        """Remove intra-modality edges, except in case of p=0 constraints"""
        lnodes = [n for n in self.lnodes() if n.modality == modality]
        for i,l in enumerate(lnodes):
            for L in lnodes[i+1:]:
                if self.has_edge(l, L):
                    if self[l][L][PROBABILITY] != 0.:
                        self.remove_edge(l, L)
    
    def remove_crossmodal_edges(self, modality1, modality2):
        tnodes = self.tnodes()
        tnodes1 = [n for n in tnodes if n.modality == modality1]
        tnodes2 = [n for n in tnodes if n.modality == modality2]
        for t1 in tnodes1:
            for t2 in tnodes2:
                if self.has_edge(t1, t2):
                    self.remove_edge(t1, t2)
    
    def remove_track_nodes(self, modality):
        tnodes = self.tnodes()
        tnodes = [n for n in tnodes if n.modality == modality]
        self.remove_nodes_from(tnodes)
    
    
    def remove_identity_nodes(self, threshold=0.001):
        """Remove identity nodes with incoming probabilities smaller than threshold
        
        Parameters
        ----------
        
        
        """
        inodes = [inode for inode in self.inodes()
                        if max([self[inode][n][PROBABILITY] 
                                for n in self.neighbors(inode)]) < threshold]
        self.remove_nodes_from(inodes)
    
    
    def to_annotation(self):
        
        tnodes = [n for n,d in self.nodes_iter(data=True) \
                        if isinstance(n, TrackNode) \
                        and not d.get(SUBTRACK, False)]
        inodes = [n for n in self if isinstance(n, IdentityNode)]
        
        modalities = set([n.modality for n in tnodes])
        uris = set([n.uri for n in tnodes])
        
        annotations = {}
        for modality in modalities:
            for uri in uris:
                _tnodes = [n for n in tnodes 
                             if n.modality == modality and n.uri == uri]
                A = Annotation(uri=uri, modality=modality)
                for tnode in _tnodes:
                    p = 0.
                    n = None
                    for inode in inodes:
                        if not self.has_edge(tnode, inode):
                            continue
                        if self[tnode][inode][PROBABILITY] > p:
                            n = inode
                            p = self[tnode][inode][PROBABILITY]
                    if n is None:
                        A[tnode.segment, tnode.track] = Unknown()
                    else:
                        A[tnode.segment, tnode.track] = n.identifier
                
                annotations[uri, modality] = A
        
        return annotations
        
        
        

class SegmentationGraph(object):
    """Segmentation graph (one node per track, no edge)
    
    [T]
    
    - one node per track
    """
    def __init__(self):
        super(SegmentationGraph, self).__init__()
    
    def __call__(self, annotation):
        
        assert isinstance(annotation, Annotation), \
               "%r is not an annotation" % annotation
        
        G = MultimodalProbabilityGraph()
        u = annotation.uri
        m = annotation.modality
        
        # track nodes, track/label and label/ID edges
        for s,t,l in annotation.iterlabels():
            tnode = TrackNode(u,m,s,t)
            G.add_node(tnode, **{SUBTRACK: False})
        
        return G


class AnnotationGraph(object):
    """Annotation graph
    
    [T] === [L] === [I]
    
    - one node per track (track node, [T])
    - one label node per cluster (label node, [L])
    - one node per identity (identity node, [I])
    - one hard edge between a track and its label (p=1, ===)
    - one hard edge between a label and its known identity (p=1, ===)
    
    Parameters
    ----------
    diarization : bool, optional
        When True, labels are considered anonymous so no identity node
        is added.
    
    """
    def __init__(self, diarization=False, **kwargs):
        super(AnnotationGraph, self).__init__()
        self.diarization = diarization
    
    def __call__(self, annotation):
        
        assert isinstance(annotation, Annotation), \
               "%r is not an annotation" % annotation
        
        G = MultimodalProbabilityGraph()
        u = annotation.uri
        m = annotation.modality
        
        # identity nodes
        inodes = {l: IdentityNode(l) for l in annotation.labels()}
        # label nodes
        lnodes = {l: LabelNode(u,m,l) for l in annotation.labels()}
        
        # track nodes, track/label and label/ID edges
        for s,t,l in annotation.iterlabels():
            # track/label edge
            tnode = TrackNode(u,m,s,t)
            G.update_edge(tnode, lnodes[l], **{PROBABILITY: 1.})
            # add id node in case of 
            if (not self.diarization) and (not isinstance(l, Unknown)):
                G.update_edge(lnodes[l], inodes[l], **{PROBABILITY: 1.})
        
        # cooccurring clusters are marked as such
        K = Cooccurrence(annotation, annotation)
        for l, L, k in K:
            if l == L:
                continue
            if k>0:
                G.update_edge(lnodes[l], lnodes[L], **{PROBABILITY: 0,
                                                         COOCCURRING: True})
        
        return G


class DiarizationGraph(AnnotationGraph):
    """Diarization (or clustering) graph
    
    [T] === [L] -x- [L]
    
    Nodes:
    - one per track (track node, [T])
    - one per cluster (label node, [L])
    Edges:
    - one hard edge between a track and its cluster (p=1, ===)
    - one (p=0, -x-) edge between cooccurring clusters
    
    """
    def __init__(self, **kwargs):
        super(DiarizationGraph, self).__init__(diarization=True)


class ScoresGraph(object):
    """Scores graph
    
    [T] --- [I]
    
    - one node per track (track node, [T])
    - one node per identity (identity node, [I])
    - one soft edge between each track and candidate identities (0<p<1, ---)
    
    Parameters
    ----------
    s2p : func, optional
        Score-to-probability function.
        Defaults to identity (p=s)
    
    """
    def __init__(self, s2p=None, **kwargs):
        super(ScoresGraph, self).__init__()
        
        if s2p is None:
            s2p = lambda s: s
        self.s2p = s2p
    
    
    def __call__(self, scores):
        
        assert isinstance(scores, Scores), \
               "%r is not a score" % scores
        
        G = MultimodalProbabilityGraph()
        u = scores.uri
        m = scores.modality
        
        # identity nodes
        inodes = {i: IdentityNode(i) for i in scores.labels()}
        
        # track nodes
        tnodes = {(s,t): TrackNode(u,m,s,t) for s,t in scores.itertracks()}
        
        probabilities = scores.map(self.s2p)
        # rank = probabilities.rank()
        
        for s,t,l,p in probabilities.itervalues():
            G.update_edge(tnodes[s,t], inodes[l], **{PROBABILITY:p})
            # G.update_edge(tnodes[s,t], inodes[l], **{PROBABILITY:p,
            #                                     RANK:rank[s,t,l]})
        
        return G



class LabelSimilarityGraph(object):
    """Label similarity graph
    
    [L] --- [L]
    
    - one node per label (label node, [L])
    - one soft edge between every two labels (0<p<1, ---)
    - edges between cooccurring labels are marked as such
    
    Parameters
    ----------
    s2p : func, optional
        Similarity-to-probability function.
        Defaults to identity (p=s)
    """
    def __init__(self, s2p=None, **kwargs):
        super(LabelSimilarityGraph, self).__init__()
        
        if s2p is None:
            s2p = lambda s: s
        self.s2p = s2p
        
        # setup model
        MMx = self.getMx(BaseModelMixin)
        if len(MMx) == 0:
            raise ValueError('Missing model mixin (MMx).')
        elif len(MMx) > 1:
            raise ValueError('Too many model mixins (MMx): %s' % MMx)
        self.mmx_setup(**kwargs)
    
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
    
    
    def __call__(self, diarization, feature):
        
        assert isinstance(diarization, Annotation), \
               "%r is not an annotation" % diarization
        
        # list of labels in diarization
        labels = diarization.labels()  
            
        # label similarity matrix
        P = self.mmx_similarity_matrix(labels, annotation=diarization,
                                               feature=feature)
        # change it into a probability matrix
        P.M = self.s2p(P.M)
        
        # label cooccurrence matrix
        K = Cooccurrence(diarization, diarization)
        
        G = MultimodalProbabilityGraph()
        u = diarization.uri
        m = diarization.modality
        
        lnodes = {l: LabelNode(u,m,l) for l in labels}
        
        for i, l in enumerate(labels):
            G.add_node(lnodes[l])
            for L in labels[i+1:]:
                try:
                    # raises an exception when similarity is not available
                    G.update_edge(lnodes[l], lnodes[L], 
                                    **{PROBABILITY: P[l,L], 
                                       COOCCURRING: K[l,L] > 0})
                except Exception, e:
                    # do not add any edge if that happens
                    pass
        
        return G


class TrackCooccurrenceGraph(object):
    """Track cooccurrence graph
    
    [Ta]
     ||
    [ta] --- [tb]
    
    - one node per sub-track in first modality (track node, [T])
    - one node per track in second modality (track node, [t])
    - one soft edge between every two cooccurring tracks [T] and [t]
    
    Parameters
    ----------
    P : DataFrame, optional
        Probability for two tracks to be the same person based on the number
        of cooccurring tracks in both modalities P[n, m]
    modalityA, modalityB : str, optional
        Names of first and second modalities
    min_duration : float, optional
        Minimum duration of a track for it to be used in probability estimation
    significant : float, optional
        Minimum overall duration of cooccurrence for a combination to be 
        considered as significant.
    
    """
    def __init__(self, modalityA=None, modalityB=None,
                       P=None, min_duration=0., significant=0., **kwargs):
        
        super(TrackCooccurrenceGraph, self).__init__()
        
        if P is not None:
            assert isinstance(P, DataFrame), \
                   "%r is not a DataFrame" % P
            self.P = P
        
        assert isinstance(min_duration, float), \
               "%r is not a float" % min_duration
        self.min_duration = min_duration
        
        assert isinstance(significant, float), \
               "%r is not a float" % significant
        self.significant = significant
        
        self.modalityA = modalityA
        self.modalityB = modalityB
    
    def _AB2ab(self, A, B):
        """
        
        Parameters
        ----------
        A : Annotation
        B : Annotation
        
        Returns
        -------
        timeline : Timeline
        a : Annotation
        b : Annotation
        
        """
        tl = (A.timeline + B.timeline).segmentation()
        tl = Timeline([s for s in tl if s.duration > self.min_duration], 
                      uri=tl.uri)
        a = A >> tl
        b = B >> tl
        return tl, a, b
    
    def fit(self, annotations):
        """
        
        Parameters
        ----------
        annotations : (Annotation, Annotation) iterator
        
        Returns
        -------
        
        
        """
        
        # possible_match[n, m] is the total possible match duration
        # when there are n A-tracks & m B-tracks
        possible_match = DataFrame()
        
        # actual_match[n, m] is the total actual match duration
        # when there are n A-tracks & m B-tracks
        actual_match = DataFrame()
        
        # overlap[n, m] is the total duration 
        # when there are n A-tracks & m B-tracks
        overlap = DataFrame()
        
        for n, (A, B) in enumerate(annotations):
            
            assert isinstance(A, Annotation), "%r is not an Annotation" % A
            assert isinstance(B, Annotation), "%r is not an Annotation" % B
            if n == 0:
                self.modalityA = A.modality
                self.modalityB = B.modality
            else:
                assert A.modality == self.modalityA, \
                       "bad modality (%r, %r)" % (self.modalityA, A.modality)
                assert B.modality == self.modalityB, \
                       "bad modality (%r, %r)" % (self.modalityB, B.modality)
            assert A.uri == B.uri, \
                   "resource mismatch (%r, %r)" % (A.uri, B.uri)
            
            timeline, a, b = self._AB2ab(A, B)
            
            for segment in timeline:
                
                duration = segment.duration
                
                # number of tracks 
                atracks = a.tracks(segment)
                Na = len(atracks)
                btracks = b.tracks(segment)
                Nb = len(btracks)
                
                if Na == 0 or Nb == 0:
                    continue
                
                # number of matching tracks
                N = len(a.get_labels(segment) & b.get_labels(segment))
                
                # increment possible_match & actual_match
                try:
                    p_m = possible_match.get_value(Na, Nb)
                    a_m = actual_match.get_value(Na, Nb)
                    ovl = overlap.get_value(Na, Nb)
                except Exception, e:
                    p_m = 0.
                    a_m = 0.
                    ovl = 0.
                
                possible_match = possible_match.set_value(Na, Nb,
                                                          p_m + min(Na,Nb)*duration)
                actual_match = actual_match.set_value(Na, Nb,
                                                      a_m + N*duration)
                overlap = overlap.set_value(Na, Nb, ovl + duration)
        
        self.actual_match = actual_match
        self.possible_match = possible_match
        self.raw_P = self.actual_match / self.possible_match
        self.overlap = overlap
        
        # make sure probability is smaller than 1.
        self.P = np.minimum(1-1e-6, self.raw_P)
        # remove statistically insignificant probabilities
        self.P[self.overlap < self.significant] = np.nan
        
        return self
    
    def __call__(self, A, B, only1x1=False):
        """
        
        Parameters
        ----------
        A, B : Annotation
            Annotations from two modalities
        only1x1 : bool
            When True, only add cross-modal edges when there is exactly
            one track in modality A and one track in modality B.
        
        """
        
        assert isinstance(A, Annotation), "%r is not an Annotation" % A
        assert isinstance(B, Annotation), "%r is not an Annotation" % B
        
        assert A.uri == B.uri, "resource mismatch (%r, %r)" % (A.uri, B.uri)
        
        ma = A.modality
        mb = B.modality
        assert ma == self.modalityA, \
               "bad modality (%r, %r)" % (self.modalityA, ma)
        assert mb == self.modalityB, \
               "bad modality (%r, %r)" % (self.modalityB, mb)
        
        G = MultimodalProbabilityGraph()
        u = A.uri
        
        # (modality, track)-indexed dictionaries
        # tnodes[m, t] is the set of nodes of modality m with tracks called t
        tnodes = {}
        
        # Sub-tracks graph
        # it contains only [ta] -- [tb] edges for cooccurring subtracks
        timeline, a, b = self._AB2ab(A, B)
        
        for s in timeline:
            
            # if tracks are too short, skip them
            if s.duration < self.min_duration:
                continue
            
            # Sub-tracks for current segment
            atracks = a.tracks(s)
            btracks = b.tracks(s)
            # and their number
            Na = len(atracks)
            Nb = len(btracks)
            
            # if one modality does not have any track
            # go to next segment
            if Na == 0 or Nb == 0:
                continue
            
            if only1x1 and (Na != 1 or Nb != 1):
                continue
            
            # if cross-modal probability is not available for this configuration
            # (either never seen before or not significant), go to next segment
            try:
                probability = self.P.get_value(Na, Nb)
                assert not np.isnan(probability)
            except Exception, e:
                continue
            
            # add a soft edge between each cross-modal pair of tracks
            for ta in atracks:
                
                atnode = TrackNode(u, ma, s, ta)
                
                # initialize tnodes[ma, ta] with empty set
                # if it is the first time we meet this track name
                if (ma, ta) not in tnodes:
                    tnodes[ma,ta] = set([])
                
                G.add_node(atnode, {SUBTRACK: True})
                
                # add atnode to the list of tnodes
                tnodes[ma,ta].add(atnode)
                
                for tb in btracks:
                    btnode = TrackNode(u, mb, s, tb)
                    
                    # initialize tnodes[mb, tb] with empty set
                    # if it is the first time we meet this track name
                    if (mb, tb) not in tnodes:
                        tnodes[mb,tb] = set([])
                    
                    # add btnode to the list of tnodes
                    tnodes[mb,tb].add(btnode)
                    
                    # add cross-modal edge between sub-tracks
                    if probability is not None:
                        G.add_node(btnode, {SUBTRACK: True})
                        G.update_edge(atnode, btnode, **{PROBABILITY: probability,
                                                           COOCCURRING: True})
        
        # [Ta] tracks
        # [Ta] == [ta] hard edges
        for sa,ta in A.itertracks():
            # original track
            aTnode = TrackNode(u, ma, sa, ta)
            G.add_node(aTnode, {SUBTRACK: False})
            for tnode in tnodes.get((ma,ta), []):
                # do not add self-loop (yes, this can happen)
                if tnode == aTnode:
                    continue
                G.update_edge(aTnode, tnode, **{PROBABILITY: 1., 
                                                  SUBTRACK: True})
        
        # [Tb] tracks
        # [Tb] == [tb] hard edges
        for sb,tb in B.itertracks():
            # original track
            bTnode = TrackNode(u, mb, sb, tb)
            G.add_node(bTnode, {SUBTRACK: False})
            for tnode in tnodes.get((mb,tb), []):
                # do not add self-loop (yes, this can happen)
                if tnode == bTnode:
                    continue
                G.update_edge(bTnode, tnode, **{PROBABILITY: 1., SUBTRACK: True})
        
        return G
