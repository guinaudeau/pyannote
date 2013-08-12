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

from pyannote.base.matrix import LabelMatrix, get_cooccurrence_matrix
import networkx as nx
import numpy as np
import scipy.stats
import scipy.optimize
from matplotlib import pyplot as plt


def label_clustering_groundtruth(reference, hypothesis):
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
    C = get_cooccurrence_matrix(hypothesis, reference)

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



class Binarizer(object):
    def __init__(self, threshold=1., comparison="=="):
        super(Binarizer, self).__init__()
        self.threshold = threshold
        self.comparison = comparison

    def __call__(self, x):

        if self.comparison == "==":
            return 1. * (x == self.threshold)
        elif self.comparison == "!=":
            return 1. * (x != self.threshold)
        elif self.comparison == "<":
            return 1. * (x < self.threshold)
        elif self.comparison == "<=":
            return 1. * (x <= self.threshold)
        elif self.comparison == ">":
            return 1. * (x > self.threshold)
        elif self.comparison == ">=":
            return 1. * (x >= self.threshold)



class LogisticProbabilityMaker(object):
    """
    Score to probability converter

    """
    def __init__(self, popt=None):
        super(LogisticProbabilityMaker, self).__init__()
        self.popt = popt

    def __call__(self, x):
        y = self.logistic(x, *(self.popt))
        return np.maximum(np.minimum(y, 1-1e-6), 1e-6)

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

        # remove NaN and infinity
        finite = np.isfinite(X)
        X = X[finite]
        y = y[finite]

        # extract positive/negative similarity samples
        positives = X[np.where(y == 1)]
        negatives = X[np.where(y == 0)]

        if prior is None:
            prior = 1. * len(negatives) / len(positives)

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

        dcount_p, _ = scipy.histogram(positives, bins, density=True)
        dcount_n, _ = scipy.histogram(negatives, bins, density=True)

        count_p, _ = scipy.histogram(positives, bins, density=False)
        count_n, _ = scipy.histogram(negatives, bins, density=False)

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


        atleast_p = 1./(10*num_bins) * len(positives)
        atleast_n = 1./(10*num_bins) * len(negatives)

        focus = np.isfinite(X) & (count_p > atleast_p) & (count_n > atleast_n)

        x = X[focus]
        y = 1. / (1 + prior * dcount_n[focus] / dcount_p[focus])


        M = mean
        Q = 1.
        B = 1./(mean_p - mean_n)
        v = 1./prior

        # if plot:
        #     print 'init: B = %g | Q = %g | M = %g | v = %g' % (B, Q, M, v)
        #     plt.plot(bins, self.logistic(bins, B, Q, M, v), 'k--', label='init')
        #     plt.xlim(*xlim)

        self.popt, _ = scipy.optimize.curve_fit(self.logistic, x, y,
                                                p0=(B, Q, M, v),
                                                maxfev=maxfev)

        if plot:
            plt.subplot(2,1,2)
            B, Q, M, v = self.popt
            print 'popt: B = %g | Q = %g | M = %g | v = %g' % (B, Q, M, v)
            plt.plot(bins, self(bins), color='grey', linewidth=2, label='popt')
            plt.scatter(x, y, color='k')
            plt.xlim(*xlim)
            plt.ylim(0, 1)

        return self
