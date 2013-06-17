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

from pyannote.base import URI, MODALITY, SEGMENT, TRACK, LABEL, IDENTITY
from pyannote.base import Segment, Timeline, Annotation, Unknown, Scores
from pyannote.base.matrix import Cooccurrence
from pyannote.algorithm.clustering.model.base import BaseModelMixin
from pyannote.algorithm.mpg.node import IdentityNode, TrackNode
from pandas import DataFrame
import networkx as nx
import numpy as np

PROBABILITY = 'probability'
# SUBTRACK = 'subtrack'
# COOCCURRING = 'cooccurring'
# RANK = 'rank'


class MultimodalProbabilityGraph(nx.Graph):

    def __init__(self, **kwargs):
        super(MultimodalProbabilityGraph, self).__init__(**kwargs)

    def inodes(self):
        return [n for n in self if isinstance(n, IdentityNode)]

    def tnodes(self):
        return [n for n in self if isinstance(n, TrackNode)]

    def modalities(self, nbunch=None):
        if nbunch is None:
            nbunch = self.tnodes()
        return set([n.modality for n in nbunch])

    def uris(self, nbunch=None):
        if nbunch is None:
            nbunch = self.tnodes()
        return set([n.uri for n in nbunch])

    def update(self, other):
        self.add_nodes_from(other.nodes_iter(data=True))
        self.add_edges_from(other.edges_iter(data=True))
        return self

    def copy(self):
        return self.__class__().update(self)

    def add_track_constraints(self):
        """Add p=0 edges between each intra-modality pair of
        cooccurring tracks"""

        # obtain the list of all modalities in graph
        tnodes = self.tnodes()
        modalities = self.modalities(tnodes)

        for modality in modalities:
            # obtain the list of tracks for this modality
            _tnodes = [n for n in tnodes and n.modality == modality]

            # loop on each pair of tracks and check for overlapping ones
            for n, node in enumerate(_tnodes):
                for other_node in _tnodes[n+1:]:
                    # are they overlapping?
                    if node.segment.intersects(other_node.segment):
                        self.add_edge(node, other_node, **{PROBABILITY: 0.})

        return self

    def add_identity_constraints(self):
        """Add p=0 edges between each pair of identity nodes
        """
        inodes = self.inodes()
        for n, node in enumerate(inodes):
            for other_node in inodes[n+1:]:
                self.add_edge(node, other_node, **{PROBABILITY: 0.})

        return self

    def propagate_constraints(self):
        """Propagate p=0 and p=1 probabilities edges
        """

        # propagated p=1 constraints
        p1 = []
        c = nx.Graph(self)
        c.remove_edges_from([(e, f) for e, f, d in self.edges_iter(data=True)
                             if d[PROBABILITY] != 1])
        components = nx.connected_components(c)
        for component in components:
            for i, n in enumerate(component):
                for m in component[i+1:]:
                    p1.append((n, m))

        # propagated p=0 constraints
        p0 = []
        c = nx.Graph(self)
        c.remove_edges_from([(e, f) for e, f, d in self.edges_iter(data=True)
                             if d[PROBABILITY] != 0])
        c = nx.blockmodel(c, components, multigraph=True)
        for e, f in c.edges_iter():
            for n in components[e]:
                for m in components[f]:
                    p0.append((n, m))

        for n, m in p1:
            self.add_edge(n, m, **{PROBABILITY: 1.})
        for n, m in p0:
            self.add_edge(n, m, **{PROBABILITY: 0.})

        return self

    def get_tracks_by_name(self, modality, name):
        return [n for n in self.tnodes()
                if n.track == name and n.modality == modality]

    def get_tracks_by_time(self, modality, t):
        return [n for n in self.tnodes()
                if n.segment.overlaps(t) and n.modality == modality]

    def get_identity(self, name):
        return [n for n in self.inodes() if n.identifier == name][0]

    def map(self, func):
        """

        Parameters
        ----------
        func : function
            In case func(p) is NaN or inf, the correspond edge is removed.

        """
        mapped = self.__class__()
        mapped.add_nodes_from(self.nodes_iter(data=True))
        for e, f, d in self.edges_iter(data=True):
            p = func(d[PROBABILITY])
            if np.isfinite(p):
                mapped.add_edge(e, f, **{PROBABILITY: p})
        return mapped

    # def _log(self):
    #     return self.map(lambda p: -np.log(p))

    def subgraphs_iter(self, threshold=0.):

        zeros = [(e, f) for (e, f, d) in self.edges_iter(data=True)
                 if d[PROBABILITY] <= threshold]

        G = self.copy()
        G.remove_edges_from(zeros)
        components = nx.connected_components(G)

        for component in components:
            yield self.subgraph(component)

    # def shortest_path(self, inode, tnode):
    #     log = self.map(lambda p: -np.log)

    #     # remove all inodes but inode
    #     inodes = [n for n in log.inodes() if n != inode]
    #     log.remove_nodes_from(inodes)
    #     path = nx.shortest_path(log, source=inode, target=tnode,
    #                             weight=PROBABILITY)

    #     P = []
    #     s = path[0]
    #     for t in path[1:]:
    #         p = self[s][t][PROBABILITY]
    #         print "%.2f %s %s" % (p, s, t)
    #         P.append(p)
    #         s = t

    #     return path, P

    # def complete(self, tracks=False):
    #     """

    #     Parameters
    #     ----------
    #     tracks : bool
    #         If tracks is True, complete graph also contains track2track edges
    #     """

    #     # propagate constraints (on a copy) and get -log prob graph
    #     g = self.copy()
    #     g.propagate_constraints()
    #     log = g.map(lambda p: -np.log)

    #     c = MultimodalProbabilityGraph()

    #     # all track nodes of interest
    #     # ie speaker/head node not subtrack
    #     tnodes = [(n, d) for n, d in self.nodes_iter(data=True)
    #               if isinstance(n, TrackNode)
    #               and n.modality in ['speaker', 'head']
    #               and not d.get(SUBTRACK, False)]

    #     # all identity nodes
    #     inodes = [(n, d) for n, d in self.nodes_iter(data=True)
    #               if isinstance(n, IdentityNode)]

    #     # tnode/tnode shortest path (with forbidden identity nodes)
    #     _log = nx.Graph(log)
    #     _log.remove_nodes_from(zip(*inodes)[0])
    #     if tracks:
    #         _shortest = nx.shortest_path_length(_log, weight=PROBABILITY)
    #         for i, (n, d) in enumerate(tnodes):
    #             c.add_node(n, **d)
    #             for N, D in tnodes[i+1:]:
    #                 if g.has_edge(n, N):
    #                     data = dict(g[n][N])
    #                 else:
    #                     if N in _shortest[n]:
    #                         data = {PROBABILITY: np.exp(-_shortest[n][N])}
    #                     else:
    #                         data = {PROBABILITY: 0.}
    #                 c.update_edge(n, N, **data)

    #     # inode/tnodes shortest path (with forbidden other identity nodes)
    #     for i, (n, d) in enumerate(inodes):
    #         c.add_node(n, **d)
    #         _log = nx.Graph(log)
    #         _log.remove_nodes_from([m for j, (m, _) in enumerate(inodes)
    #                                 if j != i])
    #         _shortest = nx.shortest_path_length(_log, source=n, weight=PROBABILITY)
    #         for N, D in tnodes:
    #             c.add_node(N, **D)
    #             if N not in _shortest:
    #                 continue
    #             if g.has_edge(n, N):
    #                 data = dict(g[n][N])
    #             else:
    #                 data = {PROBABILITY: np.exp(-_shortest[N])}
    #             c.update_edge(n, N, **data)

    #     # inode/inode constraint
    #     c.add_identity_constraints()

    #     return c


    # def remove_recognition_edges(self, modality):
    #     inodes = self.inodes()
    #     tnodes = [n for n in self.tnodes() if n.modality == modality]
    #     for t in tnodes:
    #         for i in inodes:
    #             if self.has_edge(t, i):
    #                 self.remove_edge(t, i)

    # def remove_diarization_edges(self, modality):
    #     """Remove intra-modality edges, except in case of p=0 constraints"""
    #     lnodes = [n for n in self.lnodes() if n.modality == modality]
    #     for i, l in enumerate(lnodes):
    #         for L in lnodes[i+1:]:
    #             if self.has_edge(l, L):
    #                 if self[l][L][PROBABILITY] != 0.:
    #                     self.remove_edge(l, L)

    # def remove_crossmodal_edges(self, modality1, modality2):
    #     tnodes = self.tnodes()
    #     tnodes1 = [n for n in tnodes if n.modality == modality1]
    #     tnodes2 = [n for n in tnodes if n.modality == modality2]
    #     for t1 in tnodes1:
    #         for t2 in tnodes2:
    #             if self.has_edge(t1, t2):
    #                 self.remove_edge(t1, t2)

    # def remove_track_nodes(self, modality):
    #     tnodes = self.tnodes()
    #     tnodes = [n for n in tnodes if n.modality == modality]
    #     self.remove_nodes_from(tnodes)

    # def remove_identity_nodes(self, threshold=0.001):
    #     """Remove identity nodes with incoming probabilities smaller than threshold

    #     Parameters
    #     ----------


    #     """
    #     inodes = [inode for inode in self.inodes()
    #               if max([self[inode][n][PROBABILITY]
    #               for n in self.neighbors(inode)]) < threshold]
    #     self.remove_nodes_from(inodes)

    # def to_annotation(self):

    #     tnodes = [n for n, d in self.nodes_iter(data=True)
    #               if isinstance(n, TrackNode)
    #               and not d.get(SUBTRACK, False)]
    #     inodes = [n for n in self if isinstance(n, IdentityNode)]

    #     modalities = self.modalities()
    #     uris = self.uris()

    #     annotations = {}
    #     for modality in modalities:
    #         for uri in uris:
    #             _tnodes = [n for n in tnodes
    #                        if n.modality == modality and n.uri == uri]
    #             A = Annotation(uri=uri, modality=modality)
    #             for tnode in _tnodes:
    #                 p = 0.
    #                 n = None
    #                 for inode in inodes:
    #                     if not self.has_edge(tnode, inode):
    #                         continue
    #                     if self[tnode][inode][PROBABILITY] > p:
    #                         n = inode
    #                         p = self[tnode][inode][PROBABILITY]
    #                 if n is None:
    #                     A[tnode.segment, tnode.track] = Unknown()
    #                 else:
    #                     A[tnode.segment, tnode.track] = n.identifier

    #             annotations[uri, modality] = A

    #     return annotations

    # def to_json(self):

    #     nodes = self.nodes()
    #     N = len(nodes)

    #     nodes_json = [node.to_json() for node in nodes]

    #     links_json = []
    #     for n, node in enumerate(nodes):
    #         for m in range(n+1, N):
    #             other_node = nodes[m]
    #             if not self.has_edge(node, other_node):
    #                 continue
    #             links_json.append({'source': n,
    #                                'target': m,
    #                                PROBABILITY: self[node][other_node][PROBABILITY]})

    #     return {'nodes': nodes_json, 'links': links_json}


class SegmentationGraph(object):
    """Segmentation graph (one node per track, no edge)

    [T]

    - one node per track
    """
    def __init__(self):
        super(SegmentationGraph, self).__init__()

    def __call__(self, annotation):

        G = MultimodalProbabilityGraph()
        u = annotation.uri
        m = annotation.modality

        for s, t in annotation.itertracks():
            G.add_node(TrackNode(**{URI: u,
                                    MODALITY: m,
                                    SEGMENT: s,
                                    TRACK: t}))

        return G


class AnnotationGraph(object):
    """Annotation graph

    [T] === [I]

    - one node per track (track node, [T])
    - one node per identity (identity node, [I])
    - one hard edge between a track and its known identity (p=1, ===)
    - one hard edge between each pair of tracks with the same label

    """
    def __init__(self, **kwargs):
        super(AnnotationGraph, self).__init__()

    def __call__(self, annotation):

        G = MultimodalProbabilityGraph()
        u = annotation.uri
        m = annotation.modality

        # identity nodes
        inodes = {l: IdentityNode(l) for l in annotation.labels()}

        # add edges between tracks and identities
        for s, t, l in annotation.iterlabels():

            tnode = TrackNode(**{URI: u, MODALITY: m, SEGMENT: s, TRACK: t})
            G.add_node(tnode)

            if not isinstance(l, Unknown):
                G.add_edge(tnode, inodes[l], **{PROBABILITY: 1.})

        # add hard edges between tracks with the same identity

        tnodes = G.tnodes()
        for i, n in enumerate(tnodes):

            s = n.segment
            t = n.track
            l = annotation[s, t]

            for N in tnodes[i+1:]:

                S = N.segment
                T = N.track
                L = annotation[S, T]

                if l == L:
                    G.add_edge(n, N, **{PROBABILITY: 1.})

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

        G = MultimodalProbabilityGraph()
        u = scores.uri
        m = scores.modality

        # identity nodes
        inodes = {i: IdentityNode(i) for i in scores.labels()}

        # track nodes
        tnodes = {(s, t): TrackNode(**{URI: u, MODALITY: m,
                                       SEGMENT: s, TRACK: t})
                  for s, t in scores.itertracks()}

        probabilities = scores.map(self.s2p)

        for s, t, l, p in probabilities.itervalues():
            G.add_edge(tnodes[s, t], inodes[l], **{PROBABILITY: p})

        return G


class LabelSimilarityGraph(object):
    """Label similarity graph

    [T] === [T] for tracks with the same label
    [T] --- [T] for tracks with different labels
    [T] -x- [T] for tracks with different co-occurring labels

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
        MX = [Mx for Mx in cls.mro()
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
        """
        Parameters
        ----------
        diarization : Annotation
        feature : Feature
        """

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

        tnodes = [TrackNode(**{URI: u, MODALITY: m, SEGMENT: s, TRACK: t})
                  for s, t in diarization.itertracks()]

        for i, n in enumerate(tnodes):

            G.add_node(n)

            s = n.segment
            t = n.track
            l = diarization[s, t]

            for N in tnodes[i+1:]:

                S = N.segment
                T = N.track
                L = diarization[S, T]

                # if two tracks have the same label
                # set probability to 1
                if l == L:
                    p = 1.
                    k = False
                # if two tracks are cooccurring
                # set probability to 0
                elif K[l, L] > 0:
                    p = 0.
                    k = True
                # otherwise, try and get the probability from probability matrix
                else:
                    k = False
                    try:
                        p = P[l, L]
                    except Exception, e:
                        p = None

                # if probability is not available, do not add any edge
                if p is not None:
                    G.add_edge(n, N, **{PROBABILITY: p})

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
        tl = (A.get_timeline().union(B.get_timeline())).segmentation()
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
                                                          p_m + min(Na, Nb)*duration)
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

        # Sub-tracks graph
        # it contains only [ta] -- [tb] edges for cooccurring subtracks
        # track names are kept unchanged
        timeline, a, b = self._AB2ab(A, B)

        for s in timeline:

            # do not add edges for very short tracks
            if s.duration < self.min_duration:
                continue

            # Sub-tracks for current sub-segment and their number
            subtracks_a = a.tracks(s)
            Na = len(subtracks_a)
            subtracks_b = b.tracks(s)
            Nb = len(subtracks_b)

            # if one modality does not have any track, go to next segment
            if Na == 0 or Nb == 0:
                continue

            # if one modality has more than one coocurring track
            # and option only1x1 is ON, go to next segment
            if only1x1 and (Na != 1 or Nb != 1):
                continue

            # if cross-modal probability is not available for this configuration
            # (either never seen before or not significant), go to next segment
            try:
                probability = self.P.get_value(Na, Nb)
                assert not np.isnan(probability)
            except Exception, e:
                continue

            # get original track corresponding to each subtrack
            tracks_A = set([])
            for t in subtracks_a:
                for S, T in A.get_track_by_name(t):
                    if s in S:
                        tracks_A.add((S, T))
            tracks_B = set([])
            for t in subtracks_b:
                for S, T in B.get_track_by_name(t):
                    if s in S:
                        tracks_B.add((S, T))

            # add edges between co-occurring tracks
            for sA, tA in tracks_A:
                node_A = TrackNode(u, ma, sA, tA)
                for sB, tB in tracks_B:
                    node_B = TrackNode(u, mb, sB, tB)
                    G.add_edge(node_A, node_B, **{PROBABILITY: probability})

        return G


import math


class GetProbSpoken2Speaker:

    def __init__(self, fileName='/vol/work1/roy/repere/spk/probs.txt', tmax=500):
        with open(fileName, 'r') as f:
            data = f.read()
        data = [float(val) for val in data[0:-1].split('\n')]
        self.alpha = data[0]
        self.delta = data[1]
        self.prob = data[2:]
        self.tmax = tmax

    def __call__(self, sA, sB):
        # First, check if time difference is more than tmax (=500s). If so, return (-1).
        # to indicate that the probability between these two nodes CANNOT be
        # estimated robustly, so these two nodes should NOT be linked.
        ta = sA.start
        tb = sA.end
        tc = sB.start
        td = sB.end
        if (td-ta) > self.tmax or (tb - tc) > self.tmax:
            return -1
        t1 = ta
        P = 0  # prob.
        N = 0  # No. of time links from (ta,tb) to (tc,td) with a time step of delta.
        while (t1 <= tb):
            tc_ = int(round((tc - t1) / self.delta, 0) - self.alpha)
            td_ = int(round((td - t1) / self.delta, 0) - self.alpha)
            P += math.fsum(self.prob[tc_:td_+1])
            N += (td_ - tc_ + 1)
            t1 += self.delta
        P /= N
        return P


class CrossModalGraph(object):

    def __init__(self, fileName='/vol/work1/roy/repere/spk/probs.txt',
                 modalityA=None, modalityB=None, tmax=500, **kwargs):
        super(CrossModalGraph, self).__init__()
        self.modalityA = modalityA
        self.modalityB = modalityB
        self.get_prob = GetProbSpoken2Speaker(fileName=fileName, tmax=tmax)

    def __call__(self, A, B, **kwargs):
        assert isinstance(A, Annotation), "%r is not an Annotation" % A
        assert isinstance(B, Annotation), "%r is not an Annotation" % B
        assert A.uri == B.uri, "resource mismatch (%r, %r)" % (A.uri, B.uri)

        mA = A.modality
        mB = B.modality
        assert mA == self.modalityA, \
            "bad modality (%r, %r)" % (self.modalityA, mA)
        assert mB == self.modalityB, \
            "bad modality (%r, %r)" % (self.modalityB, mB)

        G = MultimodalProbabilityGraph()
        u = A.uri

        for sA, tA in A.itertracks():
            nA = TrackNode(u, mA, sA, tA)
            for sB, tB in B.itertracks():
                nB = TrackNode(u, mB, sB, tB)
                p = self.get_prob(sA, sB)
                if p != -1:
                    G.add_edge(nA, nB, **{PROBABILITY: p})

        return G
