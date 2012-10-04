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

"""Clustering utility functions"""

from pyannote.base.matrix import LabelMatrix, Cooccurrence
import networkx as nx
import numpy as np
import scipy.stats
import scipy.optimize
from matplotlib import pyplot as plt


def get_label_groundtruth(reference, hypothesis):
    """
    Get label clustering grountruth matrix
    
    This is a square matrix M indexed by hypothesis labels.
    
    M[label1, label2] takes the following value:
        *  1 if hypothesis tracks labelled with label1 and label2 
           are from the same person according to the reference,
        *  0 if they are from two different persons according to the reference,
        * -1 in case of ambiguity.
    
    Parameters
    ----------
    reference : Annotation
        Reference annotation where tracks from the same person share the same
        unique label.
    hypothesis : Annotation
        Hypothesis annotation given as input of a clustering algorithm.
    
    Returns
    -------
    matrix : LabelMatrix
        Square matrix indexed by hypothesis labels with values in {-1, 0, 1}.
    """
    
    # list of labels from hypothesis
    hlabels = hypothesis.labels()
    
    # label cooccurrence matrix
    C = Cooccurrence(hypothesis, reference)
        
    # coocurrence graph
    g = nx.Graph()
    for hlabel, rlabel, duration in C:
        # node for hypothesis label
        hnode = ('h', hlabel)
        # node for reference label
        rnode = ('r', rlabel)
        # link cooccurring hypothesis and reference labels
        if duration > 0:
            g.add_edge(hnode, rnode)
    
    # note that hypothesis labels not cooccurring with any reference label
    # are not added to the graph.
    # similarly, reference labels not cooccurring with any hypothesis label
    # are not added either.
    
    # label groundtruth matrix
    # -1 means "do not know anything about those two labels"
    # 0 means "those two labels are from different persons"
    # 1 means "those two labels are from the same person"
    G = LabelMatrix(hlabels, hlabels, dtype=int, default=-1)
    
    # Make sure the diagonal is full or 1s
    for label in hlabels:
        G[label, label] = 1
    
    # Connected components in cooccurrence graph
    CC = nx.connected_components(g)
    
    # two hypothesis labels located in two different connected components
    # must be from two different persons
    for c, component in enumerate(CC):
        for other_component in CC[c+1:]:
            for node_type, label in component:
                # cooccurrence graph contains reference labels
                # that are not of interest here...
                if node_type == 'r':
                    continue
                for other_node_type, other_label in other_component:
                    # cooccurrence graph contains reference labels
                    # that are not of interest here...
                    if other_node_type == 'r':
                        continue
                    # two hypothesis labels located in two different connected
                    # components are from two different persons
                    G[label, other_label] = 0
                    G[other_label, label] = 0
    
    # hypothesis labels cooccurring with more than one reference label 
    # are ambiguous: remove them from the graph before going further
    ambiguous = [node for node, degree in g.degree_iter() if degree > 1
                                                         and node[0] == 'h']
    g.remove_nodes_from(ambiguous)
    
    # Connected components in resulting cooccurrence graph
    CC = nx.connected_components(g)
    
    # two hypothesis labels located in the same connected components
    # with exactly one reference labels must be from the same person
    for component in CC:
        for n, (node_type, label) in enumerate(component):
            # cooccurrence graph contains reference labels
            # that are not of interest here...
            if node_type == 'r':
                continue
            for other_node_type, other_label in component[n+1:]:
                # cooccurrence graph contains reference labels
                # that are not of interest here...
                if other_node_type == 'r':
                    continue
                # two hypothesis labels located in the same connected components
                # with exactly one reference labels are from the same person
                G[label, other_label] = 1
                G[other_label, label] = 1
    
    # two hypothesis labels located in two different connected components
    # must be from two different persons
    for c, component in enumerate(CC):
        for other_component in CC[c+1:]:
            for node_type, label in component:
                # cooccurrence graph contains reference labels
                # that are not of interest here...
                if node_type == 'r':
                    continue
                for other_node_type, other_label in other_component:
                    # cooccurrence graph contains reference labels
                    # that are not of interest here...
                    if other_node_type == 'r':
                        continue
                    # two hypothesis labels located in two different connected
                    # components are from two different persons
                    G[label, other_label] = 0
                    G[other_label, label] = 0
    
    return G





class LogisticProbabilityMaker(object):
    """
    Score to probability converter
    
    """
    def __init__(self, popt=None):
        super(LogisticProbabilityMaker, self).__init__()
        self.popt = popt
    
    def __call__(self, x):
        return self.logistic(x, *(self.popt))
    
    def logistic(self, x, B, Q, M, v):
        y = 1. / (1. + Q *  np.exp(-B*(x-M)))**(1./v)
        return y
    
    def fit(self, X, y, prior=None, plot=False, maxfev=10000):
        """
        Fit internal parameters to training data
        
        
        Parameters
        ----------
        X : 
        
        y : 1-d numpy array (filled with 0s, 1s and -1s)
        
        prior : float, optional
            Ratio of prior probability P_neg/P_pos. Defaults to #neg/#pos
        plot : bool, optional
            Set it to True to get a beautiful matplotlib rendering
        maxfev : integer, optional
            Passed to `curve_fit`. Increase it if the latter does not converge.
        
        """
        if plot:
            plt.ion()
            plt.figure()
        
        # extract positive/negative similarity samples
        positives = X[np.where(y == 1)]
        negatives = X[np.where(y == 0)]
        
        if prior is None:
            prior = 1. * len(negatives) / len(positives)
        
        # mean_p = np.mean(positives)
        # std_p = np.std(positives)
        # mean = mean_p
        # std = std_p
        
        mean_p = np.mean(positives)
        std_p = np.std(positives)
        mean_n = np.mean(negatives)
        std_n = np.std(negatives)
        norm_p = scipy.stats.norm(loc=mean_p, scale=std_p)
        norm_n = scipy.stats.norm(loc=mean_n, scale=std_n)
        mean = scipy.optimize.bisect(lambda t: norm_p.pdf(t)-norm_n.pdf(t), 
                                     min(mean_p, mean_n), 
                                     max(mean_p, mean_n))
        std = max(std_p, std_n)
        
        
        norm = scipy.stats.norm(loc=mean, scale=std)
        num_bins = 50
        bins = norm.ppf(np.arange(0, 1+1./num_bins, 1./num_bins))
        
        count_p, _ = scipy.histogram(positives, bins, density=True)
        count_n, _ = scipy.histogram(negatives, bins, density=True)
        
        X = .5*(bins[1:] + bins[:-1])
        
        if plot:
            plt.subplot(2,1,1)
            _, _, _ = plt.hist(negatives, bins, normed=True, 
                               color='r', alpha=0.5)
            _, _, _ = plt.hist(positives, bins, normed=True, 
                               color='g', alpha=0.5)
            plt.legend(['Inter-cluster distance', 'Intra-cluster distance'],
                       loc='upper left')
            xlim = plt.xlim()
        
        Y = 1. / (1 + prior * count_n / count_p)
        
        if plot:
            plt.subplot(2,1,2)
            plt.scatter(X, Y, color='k')
        
        focus = np.isfinite(X) & np.isfinite(Y) & \
                (X > mean_p-std_p) & (X < mean_p+std_p)
        x = X[focus]
        y = Y[focus]
        
        M = mean
        Q = 1.
        B = 1./(mean_p - mean_n)
        v = 1./prior
        
        if plot:
            print 'init: B = %g | Q = %g | M = %g | v = %g' % (B, Q, M, v)
            plt.plot(bins, self.logistic(bins, B, Q, M, v), 'k--', label='init')
            plt.xlim(*xlim)
        
        self.popt, _ = scipy.optimize.curve_fit(self.logistic, x, y,
                                                p0=(B, Q, M, v),
                                                maxfev=maxfev)
        
        if plot:
            B, Q, M, v = self.popt
            print 'popt: B = %g | Q = %g | M = %g | v = %g' % (B, Q, M, v)
            plt.plot(bins, self(bins), 'b', label='popt')
            plt.xlim(*xlim)
            plt.ylim(0, 1)
            loc = 'upper right' if mean_p < mean_n else 'upper left'
            plt.legend(loc=loc)
            
        return self

# def _estimate_label_duration_distribution(annotations, law, floc, fscale):
#     durations = np.empty((0,))
#     for A in annotations:
#         D = A._timeline.duration()
#         d = np.array([A.label_duration(L) for L in A.labels()])
#         d /= D
#         durations = np.concatenate((durations, d), axis=0)
#     params = law.fit(durations, floc=floc, fscale=fscale)
#     return params
# 
# def estimate_prior_probability(annotations, law=scipy.stats.beta, floc=None, fscale=None):
#     """Estimate clustering prior probability based on distribution of label durations
#     
#     Parameters
#     ----------
#     annotations : list of :class:`pyannote.Annotation`
#         Groundtruth annotations.
#     law : scipy.stats.rv_continuous, optional
#         How to model distribution of label durations.
#         Defaults to scipy.stats.beta
#         
#     Returns
#     -------
#     prior : float
#         Clustering prior probability
#     """
#     params = _estimate_label_duration_distribution(annotations, law, floc, fscale)
#     prior = law.expect(lambda d: d*d, args=params)
#     return prior
# 
# 
# from pyannote.algorithm.mapping import ConservativeDirectMapper
# from pyannote.base.mapping import ManyToOneMapping
# from pyannote.base.matrix import LabelMatrix
# 
# def _get_pn_scores(clustering, R, H, F):
#     mapper = ConservativeDirectMapper()
#     mapping = ManyToOneMapping.fromMapping(mapper(H, R))
#     # remove all labels with no found mapping
#     _mapping = mapping.empty()
#     for l, r in mapping:
#         if r:
#             _mapping += (l, r)
#     mapping = _mapping
#     
#     # C[i, j] = True iff labels i & j should be in the same cluster
#     C = LabelMatrix(dtype=bool, default=False)
#     for labels, _ in mapping:
#         for i in labels:
#             for j in labels:
#                 C[i, j] = True
#     
#     if not C:
#         return np.empty((0,)), np.empty((0,))
#     
#     # Get clustering scores (and sort them according to C)
#     # (visualization should show clusters as blocks on the diagonal)
#     clustering.start(H, F)
#     scores = clustering.imx_matrix[set(C.labels[0]), set(C.labels[0])]
#     n = scores.M[np.where(C.M == False)]
#     p = scores.M[np.where(C.M == True)]
#     
#     return p, n
# 
# def estimate_likelihood_ratio(uris, get_ref, get_hyp, get_features, clustering):
#     """
#     
#     Parameters
#     ----------
#     uris : list
#         List of URIs to use for estimation
#     get_ref : func
#         get_ref(uri) = reference
#     get_hyp : func
#         get_hyp(uri) = hypothesis
#     get_features : func
#         get_features(uri) = features
#     clustering : 
#         Clustering algorithm
#     
#     Returns
#     -------
#     llr : func
#         Function that returns likelihood ratio p(t | H) / p(t | ~H)
#         t ==> p(t | H) / p(t | ~H)
#     """
#     
#     negatives = np.empty((0,))
#     positives = np.empty((0,))
#     mapper = ConservativeDirectMapper()
#     
#     for u, uri in enumerate(uris):
#         
#         R = get_ref(uri)
#         H = get_hyp(uri)
#         F = get_features(uri)
#         p, n = _get_pn_scores(clustering, R, H, F)
#         negatives = np.concatenate((negatives, n), axis=0)
#         positives = np.concatenate((positives, p), axis=0)
#     
#     max_min = max(np.min(positives), np.min(negatives))
#     min_max = min(np.max(positives), np.max(positives))
#     p_kde = scipy.stats.gaussian_kde(positives)
#     n_kde = scipy.stats.gaussian_kde(negatives)
#     
#     def lr(t):
#         is_scalar = False
#         if np.isscalar(t):
#             is_scalar = True
#             t = np.array([t])
#         else:
#             is_scalar = False
#             t = np.asarray(t)
#         
#         shape = t.shape
#         t = t.reshape((1, -1))
#         
#         p_t = p_kde(t)
#         n_t = n_kde(t)
#         
#         T = (p_t / n_t).reshape((1,-1))
#         
#         undefined_low = t < max_min
#         undefined_high = t > min_max
#         T[np.where(undefined_low)] = 0.
#         T[np.where(undefined_high)] = np.inf
#         
#         if is_scalar:
#             T = T[0, 0]
#         else:
#             T = T.reshape(shape)
#         return T
#     
#     return lr
