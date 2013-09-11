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

import itertools
import numpy as np
import networkx as nx
from pyannote.algorithm.pig.pig import PROBABILITY
from pyannote.base.annotation import Annotation, Unknown
from pyannote.algorithm.clustering.ilp.ilp import ILPClustering
from pyannote.algorithm.pig.vertex import IdentityVertex, InstanceVertex


class ILPPIGMining(ILPClustering):

    def __init__(self, solver='pulp'):
        super(ILPPIGMining, self).__init__(solver=solver)

    def get_get_similarity(self, pig):

        def get_similarity(v, w):
            if pig.has_edge(v, w):
                return pig[v][w][PROBABILITY]
            return np.nan

        return get_similarity

    # Unique identity constraints
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def add_unique_identity_constraints(self, pig):
        """Add unique identity constraints

        Any person instance can be connected to at most one identity.
        """

        instances = pig.get_instance_vertices()
        identities = pig.get_identity_vertices()
        self.add_exclusivity_constraints(instances, identities)

        return self

    def get_annotations(self, pig, solution):

        c = nx.Graph()

        for (I, J), same_cluster in solution.iteritems():
            c.add_node(I),
            c.add_node(J)
            if same_cluster:
                c.add_edge(I, J)

        clusters = nx.connected_components(c)

        annotations = {}
        uris = pig.get_uris()
        modalities = pig.get_modalities()

        for uri, modality in itertools.product(uris, modalities):
            annotation = Annotation(uri=uri, modality=modality)

            for cluster in clusters:

                # obtain cluster identity
                identity_vertices = [
                    v for v in cluster if isinstance(v, IdentityVertex)
                ]

                if len(identity_vertices) > 1:
                    raise ValueError(
                        'Cluster contains more than one identity.')

                if identity_vertices:
                    identity = identity_vertices[0].identity
                else:
                    identity = Unknown()

                # obtain cluster tracks
                instance_vertices = [
                    v for v in cluster
                    if isinstance(v, InstanceVertex)
                    and v.uri == uri and v.modality == modality
                ]

                for v in instance_vertices:
                    annotation[v.segment, v.track] = identity

            annotations[uri, modality] = annotation

        return annotations


# =====================================================================
# Objective functions
# =====================================================================

class UnweightedObjectiveFunction(object):

    """
    δ = argmax α ∑ δij.pij + (1-α) ∑ (1-δij).(1-pij)
                 i-j                i-j
    """

    def get_objective(self, pig, alpha=0.5, **kwargs):
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
        get_similarity = self.get_get_similarity(pig)

        intra, N = self.get_intra_cluster_similarity(pig, get_similarity)
        inter, _ = self.get_inter_cluster_dissimilarity(pig, get_similarity)

        N = max(1, N)
        objective = 1./N*(alpha*intra+(1-alpha)*inter)

        return objective


class WeightedObjectiveMixin(object):

    def get_objective(self, pig, weights=None, **kwargs):

        get_similarity = self.get_get_similarity(pig)

        objective = None

        for (modality1, modality2), weight in weights.iteritems():

            items1 = [i for i in self.items if i.modality == modality1]
            items2 = [i for i in self.items if i.modality == modality2]

            intra, N = self.get_bipartite_similarity(
                items1, items2, get_similarity)

            inter, _ = self.get_bipartite_dissimilarity(
                items1, items2, get_similarity)

            alpha = weight['alpha']
            beta = weight['beta']

            if objective is None:
                if N:
                    objective = beta/N * (alpha*intra + (1-alpha)*inter)
            else:
                if N:
                    objective += beta/N * (alpha*intra + (1-alpha)*inter)

        return objective


# =====================================================================
# Constraints
# =====================================================================

class StrictTransitivityConstraints(object):

    def set_constraints(self, pig):

        get_similarity = self.get_get_similarity(pig)

        # Reflexivity constraints
        self.add_reflexivity_constraints(pig)

        # Symmetry constraints
        self.add_symmetry_constraints(pig)

        # Strict transitivity constraints
        self.add_transitivity_constraints(pig)

        # Identity unicity constraints
        self.add_unique_identity_constraints(pig)

        # Hard constraints
        self.add_hard_constraints(pig, get_similarity)

        return self


class RelaxedTransitivityConstraints(object):

    def set_constraints(self, pig):

        get_similarity = self.get_get_similarity(pig)

        # Reflexivity constraints
        self.add_reflexivity_constraints(pig)

        # Symmetry constraints
        self.add_symmetry_constraints(pig)

        # Relaxed transitivity constraints
        identities = pig.get_identity_vertices()
        instances = pig.get_instance_vertices()
        self.add_asymmetric_transitivity_constraints(instances, identities)

        # Identity unicity constraints
        self.add_unique_identity_constraints(pig)

        # Hard constraints
        self.add_hard_constraints(pig, get_similarity)

        return self

