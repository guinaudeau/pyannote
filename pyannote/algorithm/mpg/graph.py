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
from pyannote.algorithm.mpg.node import IdentityNode, LabelNode, TrackNode
from pandas import DataFrame
import networkx as nx

PROBABILITY = 'probability'
SUBTRACK = 'subtrack'
COOCCURRING = 'cooccurring'
RANK = 'rank'

class DiarizationGraph(object):
    """Diarization (or clustering) graph
    
    [T] === [L]
    
    - one node per track (track node, [T])
    - one node per cluster (label node, [L])
    - one hard edge between a track and its cluster (p=1, ===) 
    
    """
    def __init__(self, **kwargs):
        super(DiarizationGraph, self).__init__()
        
    def __call__(self, annotation):
        
        assert isinstance(annotation, Annotation), \
               "%r is not an annotation" % annotation
        
        G = nx.Graph()
        u = annotation.uri
        m = annotation.modality
        
        # label nodes
        lnodes = {l: LabelNode(u,m,l) for l in annotation.labels()}
        
        # track nodes & track/label hard (p=1) edges
        for s,t,l in annotation.iterlabels():
            tnode = TrackNode(u,m,s,t)
            G.add_edge(tnode, lnodes[l], {PROBABILITY:1.})
        
        return G

class AnnotationGraph(object):
    """Annotation graph
    
    [T] === [L] (=== [I])
    
    
    - one node per track (track node, [T])
    - one label node per cluster (label node, [L])
    - one node per identity (identity node, [I])
    - one hard edge between a track and its label (p=1, ===)
    - one hard edge between a label and its known identity (p=1, ===)
    
    Parameters
    ----------
    unknown : bool, optional
        Add `Unknown` identity nodes for `Unknown` labels.
        By default, only known identity nodes are added.
    
    """
    def __init__(self, unknown=False, **kwargs):
        super(AnnotationGraph, self).__init__()
        self.unknown = unknown
    
    def __call__(self, annotation):
        
        assert isinstance(annotation, Annotation), \
               "%r is not an annotation" % annotation
        
        G = nx.Graph()
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
            G.add_edge(tnode, lnodes[l], {PROBABILITY: 1.})
            # label/id edge (if it is a known ID or if  )
            if (not isinstance(l, Unknown)) or self.unknown:
                G.add_edge(lnodes[l], inodes[l], {PROBABILITY: 1., RANK: 0})
        
        return G


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
        
        G = nx.Graph()
        u = scores.uri
        m = scores.modality
        
        # identity nodes
        inodes = {i: IdentityNode(i) for i in scores.labels()}
        
        # track nodes
        tnodes = {(s,t): TrackNode(u,m,s,t) for s,t in scores.itertracks()}
        
        probabilities = scores.map(self.s2p)
        rank = probabilities.rank()
        
        for s,t,l,p in probabilities.itervalues():
            G.add_edge(tnodes[s,t], inodes[l], {PROBABILITY:p,
                                                RANK:rank[s,t,l]})
        
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
        
        G = nx.Graph()
        u = diarization.uri
        m = diarization.modality
        
        lnodes = {l: LabelNode(u,m,l) for l in labels}
        
        for i, l in enumerate(labels):
            G.add_node(lnodes[l])
            for L in labels[i+1:]:
                try:
                    # raises an exception when similarity is not available
                    G.add_edge(lnodes[l], lnodes[L], 
                               {PROBABILITY: P[l,L], COOCCURRING: K[l,L] > 0})
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
        
        # make sure probability is smaller than 1.
        self.P = np.minimum(1 - 1e-6, actual_match / possible_match)
        
        # remove statistically insignificant probabilities
        self.P[overlap < self.significant] = np.nan
        
        return self
    
    def __call__(self, A, B):
        
        assert isinstance(A, Annotation), "%r is not an Annotation" % A
        assert isinstance(B, Annotation), "%r is not an Annotation" % B
        
        assert A.uri == B.uri, "resource mismatch (%r, %r)" % (A.uri, B.uri)
        
        ma = A.modality
        mb = B.modality
        assert ma == self.modalityA, \
               "bad modality (%r, %r)" % (self.modalityA, ma)
        assert mb == self.modalityB, \
               "bad modality (%r, %r)" % (self.modalityB, mb)
        
        G = nx.Graph()
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
                        G.add_edge(atnode, btnode, {PROBABILITY: probability})
                    
        
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
                G.add_edge(aTnode, tnode, {PROBABILITY: 1., SUBTRACK: True})
        
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
                G.add_edge(bTnode, tnode, {PROBABILITY: 1., SUBTRACK: True})
        
        return G
