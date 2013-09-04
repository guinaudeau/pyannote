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

from pyannote.base.matrix import LabelMatrix


class HACModel(object):

    """"""

    def __init__(self):
        super(HACModel, self).__init__()

    # ==== Clusters Models ===================================================

    def get_model(
        self, cluster,
        annotation=None, models=None, matrix=None, history=None, feature=None
    ):

        """Get model for `cluster`

        Parameters
        ----------
        cluster : hashable
            Cluster unique identifier (typically, one annotation label)
        annotation : Annotation, optional
            Annotation at current iteration
        models : dict, optional
            Cluster models at current iteration
        matrix : LabelMatrix, optional
            Cluster similarity matrix at current iteration
        history : HACHistory, optional
            Clustering history up to current iteration
        feature : Feature, optional
            Feature

        Returns
        -------
        model :

        Notes
        -----
        This method must be overriden by inheriting class.
        """

        raise NotImplementedError("Method 'get_model' must be overriden.")

    def get_models(
        self, clusters,
        annotation=None, models=None, matrix=None, history=None, feature=None
    ):

        """Get models for all clusters

        Parameters
        ----------
        clusters : iterable
            Iterable over cluster identifiers
        annotation : Annotation, optional
            Annotation at current iteration
        models : dict, optional
            Cluster models at current iteration
        matrix : LabelMatrix, optional
            Cluster similarity matrix at current iteration
        history : HACHistory, optional
            Clustering history up to current iteration
        feature : Feature, optional
            Feature

        Returns
        -------
        models : dict
            {cluster: model} dictionary for all cluster in `clusters`
        """

        return {c: self.get_model(c, annotation=annotation, models=models, matrix=matrix, history=history, feature=feature)
                for c in clusters}

    def merge_models(
        self, clusters,
        annotation=None, models=None, matrix=None, history=None, feature=None
    ):

        """Get model resulting from  merging models of all clusters

        Parameters
        ----------
        clusters : iterable
            Iterable over cluster identifiers
        annotation : Annotation, optional
            Annotation at current iteration
        models : dict, optional
            Cluster models at current iteration
        matrix : LabelMatrix, optional
            Cluster similarity matrix at current iteration
        history : HACHistory, optional
            Clustering history up to current iteration
        feature : Feature, optional
            Feature

        Returns
        -------
        model :

        Notes
        -----
        This method must be overriden by inheriting class.
        """

        raise NotImplementedError("Method 'merge_models' must be overriden.")

    # ==== Clusters Similarity ===============================================

    def get_similarity(
        self, cluster1, cluster2,
        annotation=None, models=None, matrix=None, history=None, feature=None
    ):
        """Compute similarity between two clusters

        Parameters
        ----------
        cluster1, cluster2 : hashable
            Cluster unique identifiers (typically, two annotation labels)
        annotation : Annotation, optional
            Annotation at current iteration
        models : dict, optional
            Cluster models at current iteration
        matrix : LabelMatrix, optional
            Cluster similarity matrix at current iteration
        history : HACHistory, optional
            Clustering history up to current iteration
        feature : Feature, optional
            Feature

        Notes
        -----
        This method must be overriden by inheriting class.
        """

        raise NotImplementedError("Method 'get_similarity' must be overriden.")

    def is_symmetric(self):
        """
        Returns
        -------
        symmetric : bool
            True

        Notes
        -----
        This method must be overriden by inheriting class.
        """

        raise NotImplementedError("Method 'is_symmetric' must be overriden.")

    def get_similarity_matrix(
        self, clusters,
        annotation=None, models=None, matrix=None, history=None, feature=None
    ):
        """Compute clusters similarity matrix

        Parameters
        ----------
        clusters : iterable
        annotation : Annotation, optional
            Annotation at current iteration
        models : dict, optional
            Cluster models at current iteration
        matrix : LabelMatrix, optional
            Cluster similarity matrix at current iteration
        history : HACHistory, optional
            Clustering history up to current iteration
        feature : Feature, optional
            Feature

        Returns
        -------
        matrix : LabelMatrix
            Clusters similarity matrix
        """

        # compute missing models
        models = {c: models.get(c, self.get_model(c,
                                                  annotation=annotation, models=models, matrix=matrix, history=history, feature=feature))
                  for c in clusters}

        # cluster similarity matrix
        M = LabelMatrix(
            data=None, dtype=None, rows=clusters, columns=clusters)

        # loop on all pairs of clusters
        for i, cluster1 in enumerate(clusters):
            for j, cluster2 in enumerate(clusters):

                # if similarity is symmetric, no need to compute d(j, i)
                if self.is_symmetric() and j > i:
                    break

                # compute similarity
                M[cluster1, cluster2] = self.get_similarity(
                    cluster1, cluster2, models=models,
                    annotation=annotation, feature=feature)

                # if similarity is symmetric, d(i,j) == d(j, i)
                if self.is_symmetric():
                    M[cluster2, cluster1] = M[cluster1, cluster2]

        return M
