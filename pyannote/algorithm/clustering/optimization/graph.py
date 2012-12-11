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

"""Graphical representations"""

import networkx as nx
import numpy as np
import re
from pandas import DataFrame

from pyannote.base.segment import Segment
from pyannote.base.timeline import Timeline
from pyannote.base.annotation import Unknown, Annotation, Scores
from pyannote.base.matrix import Cooccurrence
from pyannote.algorithm.clustering.model.base import BaseModelMixin

PROBABILITY = 'probability'
SUBTRACK = 'subtrack'
COOCCURRING = 'cooccurring'

class IdentityNode(object):
    """Identity node [I]
    
    Parameters
    ----------
    identifier : any hashable object
        Unique identifier.
    """
    def __init__(self, identifier):
        super(IdentityNode, self).__init__()
        self.identifier = identifier
    
    def __eq__(self, other):
        return self.identifier == other.identifier
    
    def __hash__(self):
        return hash(self.identifier)
    
    def __str__(self):
        return "%s" % (self.identifier)
    
    def short(self):
        names = re.split('[ \-_]+', str(self.identifier))
        return "".join([name[0] for name in names[:-1]]) + "." + names[-1]
        
    def __repr__(self):
        return "<IdentityNode %s>" % self.identifier



class LabelNode(object):
    """Label node [L]
    
    Parameters
    ----------
    uri : any hashable object
        Unique resource identifier
    modality : any hashable object
        Unique modality identifier
    label : any hashable object
        Unique label identifier
    """
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
        return "%s|%s" % (self.modality, self.label)
    
    def __repr__(self):
        return "<LabelNode %s>" % self


class TrackNode(object):
    """Track node [T]
    
    Parameters
    ----------
    uri : any hashable object
        Unique resource identifier
    modality : any hashable object
        Unique modality identifier
    segment : Segment
        Segment
    track : any hashable object
        Track identifier
    
    """
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
        return "%s|%s_%s" % (self.modality, self.segment, self.track)
    
    def __repr__(self):
        return "<TrackNode %s>" % self
    
    def __contains__(self, other):
        """True if `other` is a sub-track"""
        assert isinstance(other, TrackNode), \
               "%r is not a track node" % other
        
        return (other.track == self.track) & \
               (other.segment in self.segment) & \
               (other.uri == self.uri) & \
               (other.modality == self.modality)


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
    
    [T] === [I]
    
    - one node per track (track node, [T])
    - one node per known identity (identity node, [I])
    - one hard edge between a track and its identity (p=1, ===)
    
    Parameters
    ----------
    unknown : bool, optional
        Add `Unknown` identity nodes for `Unknown` labels.
        By default, only track nodes and known identity nodes are added.
    
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
        
        # track nodes & track/identity hard (p=1) edges
        for s,t,l in annotation.iterlabels():
            tnode = TrackNode(u,m,s,t)
            G.add_node(tnode)
            if isinstance(l, Unknown):
                if self.unknown:
                    G.add_edge(tnode, inodes[l], {PROBABILITY: 1.})
            else:
                G.add_edge(tnode, inodes[l], {PROBABILITY: 1.})
        
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
    nbest : int, optional
        Only add `nbest` best identity nodes
    
    """
    def __init__(self, s2p=None, nbest=None, **kwargs):
        super(ScoresGraph, self).__init__()
        
        if s2p is None:
            s2p = lambda s: s
        self.s2p = s2p
        
        assert isinstance(nbest, int) or nbest is None, \
               "%r is not an integer" % nbest
        self.nbest = nbest
    
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
        
        # keep n-best identities
        if self.nbest is None:
            probabilities = scores.map(self.s2p)
        else:
            probabilities = scores.map(self.s2p).nbest(self.nbest)
        
        for s,t,l,p in probabilities.itervalues():
            G.add_edge(tnodes[s,t], inodes[l], {PROBABILITY:p})
        
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
                G.add_edge(aTnode, tnode, {PROBABILITY: 1., SUBTRACK: True})
        
        # [Tb] tracks
        # [Tb] == [tb] hard edges
        for sb,tb in B.itertracks():
            # original track
            bTnode = TrackNode(u, mb, sb, tb)
            G.add_node(bTnode, {SUBTRACK: False})
            for tnode in tnodes.get((mb,tb), []):
                G.add_edge(bTnode, tnode, {PROBABILITY: 1., SUBTRACK: True})
        
        return G




def add_unique_identity_constraint(G):
    """Add p=0. edges between all pairs of identity nodes"""
    inodes = [node for node in G if isinstance(node, IdentityNode)]
    for n, node in enumerate(inodes):
        for other_node in inodes[n+1:]:
            G.add_edge(node, other_node, {PROBABILITY: 0.})
    return G

def add_twin_tracks_constraint(G):
    """Add p=0 edges between all intra-modality 
       overlapping tracks (not subtracks)
    """ 
    
    # obtain the list of all modalities in graph
    modalities = set([n.modality for n in G if isinstance(n, TrackNode)])
    
    for modality in modalities:
        # obtain the list of tracks for this modality
        # (note that subtracks are not part of this list, 
        # they are hard-linked to their main track anyway)
        tnodes = [n for n in G if isinstance(n, TrackNode) \
                               and n.modality == modality \
                               and not G.node[n].get(SUBTRACK, False)]
        # loop on each pair of tracks and check for overlapping ones
        for n, node in enumerate(tnodes):
            for other_node in tnodes[n+1:]:
                # are they overlapping?
                if node.segment & other_node.segment:
                    G.add_edge(node, other_node, 
                               {PROBABILITY: 0., COOCCURRING: True})
    
    return G

def add_cooccurring_labels_contraint(G):
    
    # obtain the list of all modalities in graph
    modalities = set([n.modality for n in G if isinstance(n, LabelNode)])
    
    for modality in modalities:
        # obtain the list of labels for this modality
        lnodes = [n for n in G if isinstance(n, LabelNode) \
                               and n.modality == modality]
        # loop on each pair of labels and check if they are cooccurring
        for n, node in enumerate(lnodes):
            for other_node in lnodes[n+1:]:
                if G[node][other_node][COOCCURRING]:
                    G[node][other_node][PROBABILITY] = 0.
    
    return G
    

def meta_mpg(g):
    """Meta Multimodal Probability Graph
    
    Parameters
    ----------
    g : nx.Graph
        Multimodal probability graph
    
    Returns
    -------
    G : nx.Graph
        Multimodal probability graph where hard-linked nodes (p=1) are
        grouped into meta-nodes
    groups : list of lists
        Groups of nodes
    """
    
    # Group of hard-linked nodes
    # (ie. nodes connected with probability p=1)
    hard = nx.Graph()
    hard.add_nodes_from(g)
    hard.add_edges_from([(e,f) for e,f,d in g.edges_iter(data=True)
                               if d[PROBABILITY] == 1.])
    groups = nx.connected_components(hard)
    
    # meta graph with one node per group
    G = nx.blockmodel(g, groups, multigraph=True)
    
    meta = nx.Graph()
    for n in range(len(groups)):
        meta.add_node(n)
        for m in range(n+1, len(groups)):
            
            # do not do anything in case there is no edge
            # between those two meta-nodes
            if not G.has_edge(n, m):
                continue
            
            # obtain probabilities of all edges between n & m
            probabilities = [data[PROBABILITY] for data in G[n][m].values()]
            
            # raise an error in case of conflict (p=0 vs. p>0)
            if len(set(probabilities)) > 1 and 0 in probabilities:
                raise ValueError('conflict in meta-edges between %r and %r:' \
                                 'probabilities = %r' % (groups[n], 
                                                         groups[m], 
                                                         probabilities))
            
            meta.add_edge(n, m, {PROBABILITY: np.mean(probabilities)})
    
    return meta, groups


def draw(G, threshold=0.0):
    
    import networkx as nx
    from matplotlib import pyplot as plt
    plt.ion()
    
    pos = nx.spring_layout(G, weight=PROBABILITY)
    for e,f,d in G.edges_iter(data=True):
        probability = d[PROBABILITY]
        
        # mark 'forbidden' edges with an 'x'
        if probability == 0:
            if isinstance(e, IdentityNode) and isinstance(f, IdentityNode):
                continue
            nx.draw_networkx_edges(G, pos, edgelist=[(e,f)], 
                                           width=1., style='dotted')
            nx.draw_networkx_edge_labels(G, pos, edge_labels={(e,f): 'x'})
        
        # show 'mandatory' edges with a black thick line
        elif probability == 1:
            nx.draw_networkx_edges(G, pos, edgelist=[(e,f)], width=3.)
        
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
    plt.draw()



