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
from pyannote.algorithm.tagging import ArgMaxDirectTagger

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
    """
        
    Parameters
    ----------
    minduration : float
        Minimum duration (in seconds) for two labels to be cooccurring
    """
    
    def __init__(self, P=None, 
                       modalityA=None, modalityB=None,
                       minduration=-np.inf,
                       significant=100,
                       **kwargs):
        super(LabelCooccurrenceGraph, self).__init__()
        if P is not None:
            self.P = P
        if modalityA is not None:
            self.modalityA = modalityA
        if modalityB is not None:
            self.modalityB = modalityB
        self.minduration = minduration
        self.significant=significant
        
    def fit(self, rAiArBiB_iterator):
        """
        
        Parameters
        ----------
        rAiArBiB_iterator :(reference_A, input_A, reference_B, input_B) iterator
        
        """
        
        num_matches = LabelMatrix(dtype=int, default=0)
        num_times = LabelMatrix(dtype=int, default=0)
        
        modalityA = None
        modalityB = None
        
        argMaxDirectTagger = ArgMaxDirectTagger()
        
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
            
            
            # project all annotations to a joint timeline
            # where segments shorter that minduration are removed
            # intersection = InpA.timeline & InpB.timeline
            segmentation = (InpA.timeline + InpB.timeline).segmentation()
            timeline = Timeline([s for s in segmentation
                                   if s.duration > self.minduration
                                   and InpA._timeline.covers(s)
                                   and InpB._timeline.covers(s)],
                                video=uri)
            
            alignedInpA = InpA >> timeline
            alignedInpB = InpB >> timeline
            
            # tag as many segments as can be
            taggedInpA = argMaxDirectTagger(RefA, alignedInpA)
            taggedInpB = argMaxDirectTagger(RefB, alignedInpB)
            
            for segment in timeline:
                
                nA = len(alignedInpA[segment, :])
                nB = len(alignedInpB[segment, :])
                
                lA = taggedInpA.get_labels(segment)
                lB = taggedInpB.get_labels(segment)
                
                try:
                    num_matches[nA, nB] += len(lA & lB)
                    num_times[nA, nB] += 1
                except Exception, e:
                    num_matches[nA, nB] = len(lA & lB)
                    num_times[nA, nB] = 1
        
        self.num_matches = num_matches
        self.num_times = num_times
        self.P = LabelMatrix(dtype=float, default=np.nan)
        for nA,nB,N in self.num_times:
            if N > self.significant:
                n = self.num_matches[nA,nB]
                self.P[nA,nB] = 1.*n/(N*nA*nB)
        
        self.modalityA = modalityA
        self.modalityB = modalityB
        
        return self
    
    def __call__(self, InpA, InpB):
        
        G = nx.Graph()
        
        # make sure annotation are for the same resource
        uri = InpA.video
        if InpB.video != uri:
            raise ValueError('URI mismatch.')
        
        # make sure modalities are correct
        if InpA.modality != self.modalityA:
            raise ValueError('Modality mismatch (%s vs. %s)' \
                             % (InpA.modality, self.modalityA))
        if InpB.modality != self.modalityB:
            raise ValueError('Modality mismatch (%s vs. %s)' \
                             % (InpB.modality, self.modalityB))
        
        segmentation = (InpA.timeline + InpB.timeline).segmentation()
        timeline = Timeline([s for s in segmentation
                               if s.duration > self.minduration
                               and InpA._timeline.covers(s)
                               and InpB._timeline.covers(s)],
                            video=uri)
        
        alignedInpA = InpA >> timeline
        alignedInpB = InpB >> timeline
        
        for segment in timeline:
            
            labelsA = alignedInpA.get_labels(segment)
            labelsB = alignedInpB.get_labels(segment)
            
            nA = len(labelsA)
            nB = len(labelsB)
            
            try:
                p = self.P[nA, nB]
                if np.isnan(p):
                    continue
            except Exception, e:
                continue
            
            
            for lA in labelsA:
                nodeA = LabelNode(uri, self.modalityA, lA)
                for lB in labelsB:
                    nodeB = LabelNode(uri, self.modalityB, lB)
                    if G.has_edge(nodeA, nodeB):
                        old_p = G[nodeA][nodeB]['probability'] 
                        G[nodeA][nodeB]['probability'] = max(old_p, p)
                    else:
                        G.add_edge(nodeA, nodeB, probability=p)
        
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
        
        # list of labels in annotation
        labels = annotation.labels()  
        
        # Label similarity matrix
        P = self.mmx_similarity_matrix(labels, annotation=annotation,
                                               feature=feature)
        # Label probability matrix
        P.M = self.func(P.M)
        
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
            for other_label in labels[l+1:]:
                other_node = LabelNode(uri, modality, other_label)
                # Label-to-label edge is weighted by probability
                # or set to 0. if labels are cooccurring (the same person
                # cannot appear twice at the same time...)
                if self.cooccurring and K[label, other_label] > 0.:
                    G.add_edge(node, other_node, probability=0.)
                else:
                    try:
                        # it might happen that l/L similarity is not available
                        G.add_edge(node, other_node, 
                                   probability=P[label, other_label])
                    except Exception, e:
                        # do not add any edge if that happens
                        pass
        return G

