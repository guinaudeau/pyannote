#!/usr/bin/env python
# encoding: utf-8

# Copyright 2012-2013 Herve BREDIN (bredin@limsi.fr)

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

from pyannote.algorithm.clustering.ilp.ilp import ILPClustering
from pyannote.algorithm.diarization.bic import BICModel


class DiarizationObjectiveFunction(object):

    """
    δ = argmax α ∑ δij.pij + (1-α) ∑ (1-δij).(1-pij)
                 i-j                i-j
    """

    def get_objective(self, items, get_similarity, alpha=0.5, **kwargs):
        """
        δ = argmax α ∑ δij.pij + (1-α) ∑ (1-δij).(1-pij)
                     i∈I                i∈I
                     j∈I                j∈I

        Parameters
        ----------
        pig : PersonInstanceGraph
        alpha : float, optional
            0 ≤ α ≤ 1. Defaults to 0.5
        """
        get_similarity = self.get_get_similarity(items)

        intra, N = self.get_intra_cluster_similarity(items, get_similarity)
        inter, _ = self.get_inter_cluster_dissimilarity(items, get_similarity)

        N = max(1, N)
        objective = 1./N*(alpha*intra+(1-alpha)*inter)

        return objective


class DiarizationConstraints(object):

    def set_constraints(self, items, get_similarity):

        # Reflexivity constraints
        self.add_reflexivity_constraints(items)

        # Symmetry constraints
        self.add_symmetry_constraints(items)

        # Transitivity constraints
        self.add_transitivity_constraints(items)

        # # Hard constraints
        # self.add_hard_constraints(items, get_similarity)

        return self


class ILPDiarization(ILPClustering, DiarizationConstraints, DiarizationObjectiveFunction):

    def __init__(self, model=None, calibration=None):
        super(ILPDiarization, self).__init__()
        self.model = model
        self.calibration = calibration

    def get_get_similarity(self, matrix):

        def get_similarity(cluster1, cluster2):
            return matrix[cluster1, cluster2]

        return get_similarity

    def __call__(self, segmentation, feature):
        """
        """

        clusters = segmentation.labels()

        matrix = self.model.get_similarity_matrix(
            clusters, annotation=segmentation, feature=feature)

        if self.calibration is not None:
            matrix = self.calibration.apply(matrix)

        self.reset_problem(clusters)

        # objective function
        get_similarity = self.get_get_similarity(matrix)
        objective = self.get_objective(clusters, get_similarity)
        self.set_objective(objective)

        # constraints
        self.set_constraints(clusters, get_similarity)

        solution = self.solve()
        clusters = self.get_clusters(solution)

        translation = {}
        for cluster in clusters:
            # first element will be new cluster id
            c0 = cluster[0]
            for c in cluster[1:]:
                translation[c] = c0

        return segmentation % translation


class BICILPDiarization(ILPDiarization):

    def __init__(self, calibration, covariance_type='full', penalty_coef=3.5):
        model = BICModel(
            covariance_type=covariance_type, penalty_coef=penalty_coef)
        super(BICILPDiarization, self).__init__(model, calibration=calibration)
