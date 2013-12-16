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
from pyannote.base.annotation import Annotation, Unknown
from pyannote.algorithm.clustering.ilp.ilp import ILPClustering
from pyannote.algorithm.pig.vertex import IdentityVertex, InstanceVertex


class PIGMiningILP(ILPClustering):

    def __init__(self, solver='pulp'):
        super(PIGMiningILP, self).__init__(solver=solver)

    def get_annotations(self, pig, clusters):

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

    def __call__(self, pig, **kwargs):

        self.set_problem(pig)
        self.set_constraints(pig)
        self.set_objective(pig, pig.get_similarity, **kwargs)
        solution = self.solve()
        clusters = self.get_clusters(pig, solution)
        return self.get_annotations(pig, clusters)

# =====================================================================
# Objective functions
# =====================================================================


class PIGWeightedObjectiveMixin(object):

    def get_objective(self, pig, get_similarity, weights=None, **kwargs):

        objective = None

        for (modality1, modality2), weight in weights.iteritems():

            items1 = [i for i in pig if i.modality == modality1]
            items2 = [i for i in pig if i.modality == modality2]

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

class PIGStrictTransitivityConstraints(object):

    def set_constraints(self, pig):

        # Reflexivity constraints
        self.add_reflexivity_constraints(pig)

        # Symmetry constraints
        self.add_symmetry_constraints(pig)

        # Strict transitivity constraints
        self.add_transitivity_constraints(pig)

        # Identity unicity constraints
        instances = pig.get_instance_vertices()
        identities = pig.get_identity_vertices()
        self.add_exclusivity_constraints(instances, identities)

        # Hard constraints
        self.add_hard_constraints(pig, pig.get_similarity)

        return self


class PIGRelaxedTransitivityConstraints(object):

    def set_constraints(self, pig):

        # Reflexivity constraints
        self.add_reflexivity_constraints(pig)

        # Symmetry constraints
        self.add_symmetry_constraints(pig)

        instances = pig.get_instance_vertices()
        identities = pig.get_identity_vertices()

        # Relaxed transitivity constraints
        self.add_asymmetric_transitivity_constraints(instances, identities)

        # Identity unicity constraints
        self.add_exclusivity_constraints(instances, identities)

        # Hard constraints
        self.add_hard_constraints(pig, pig.get_similarity)

        return self
