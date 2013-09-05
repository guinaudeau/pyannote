#!/usr/bin/env python
# encoding: utf-8

# Copyright 2013 Herve BREDIN (bredin@limsi.fr)

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


from collections import namedtuple


class HACIteration(
    namedtuple('HACIteration',
               ['merged_clusters', 'similarity', 'new_cluster'])
):

    """Iteration of hierarchical agglomerative clustering

    Parameters
    ----------
    merged_clusters : iterable
        Unique identifiers of merged clusters
    similarity : float
        Similarity between merged clusters
    new_cluster : hashable
        Unique identifier of resulting clusters

    """
    def __new__(cls, merged_clusters, similarity, new_cluster):
        return super(HACIteration, cls).__new__(
            cls, merged_clusters, similarity, new_cluster)


class HACHistory(object):

    """History of hierarchical agglomerative clustering

    Parameters
    ----------
    annotation : Annotation
        Input annotation
    iterations : iterable, optional
        HAC iterations in chronological order
    """

    def __init__(self, annotation, iterations=None):
        super(HACHistory, self).__init__()
        self.annotation = annotation.copy()
        if iterations is None:
            self.iterations = []
        else:
            self.iterations = iterations

    def __len__(self):
        return len(self.iterations)

    def add_iteration(self, merged_clusters, similarity, new_cluster):
        """Add new iteration

        Parameters
        ----------
        merged_clusters : iterable
            Unique identifiers of merged clusters
        similarity : float
            Similarity between merged clusters
        new_cluster : hashable
            Unique identifier of resulting clusters

        """
        iteration = HACIteration(
            merged_clusters=merged_clusters,
            similarity=similarity,
            new_cluster=new_cluster
        )
        self.iterations.append(iteration)

    def __getitem__(self, n):
        """Get clustering status after `n` iterations

        Parameters
        ----------
        n : int
            Number of iterations

        Returns
        -------
        annotation : Annotation
            Clustering status after `n` iterations

        """
        annotation = self.annotation.copy()
        for i in xrange(n):
            iteration = self.iterations[i]
            translation = {c: iteration.new_cluster
                           for c in iteration.merged_clusters}
            annotation = annotation % translation
        return annotation
