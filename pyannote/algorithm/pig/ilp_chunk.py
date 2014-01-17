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

import logging
import numpy as np
from pyannote.base.timeline import Timeline
from pyannote.base.annotation import Annotation, Unknown
from pyannote.algorithm.pig.ilp import PIGMiningILP


class PIGMiningILPByChunk(PIGMiningILP):

    def __init__(self, solver='pulp', max_instances=None):
        super(PIGMiningILPByChunk, self).__init__(solver=solver)
        if max_instances is None:
            max_instances = np.inf
        self.max_instances = max_instances

    def _chunk(self, pig, S):
        """
        """

        n = 0

        instances = sorted(pig.get_instance_vertices())
        N = len(instances)

        while True:

            # chunk graph starting from beginning
            # and sliding towards the end
            left = n * self.max_instances / S

            right = left + self.max_instances

            focus = Timeline(
                segments=[
                    i.segment
                    for i in instances[left: min(right, N)]
                ]
            ).extent()

            yield pig.crop(focus, mode='loose'), focus.middle

            if right >= N:
                break

            n = n + 1

    def _decide(self, segment, track, hypotheses):
        # hypotheses

        counts = {}
        distance = {}

        for mid_time, label in hypotheses.iteritems():

            if isinstance(label, Unknown):
                label = Unknown

            # increment number of times this label has been selected
            counts[label] = counts.get(label, 0) + 1

            # set how close to chunk middle time the segment is
            distance[label] = min(
                distance.get(label, np.inf),
                abs(segment.middle-mid_time)
            )

        # sort labels by counts (higher first), distance (lower first)
        labels = sorted([(-counts[l], distance[l], l) for l in counts])

        # and select the first one
        label = labels[0][2]

        # if it is Unknown, instantiate it.
        if label == Unknown:
            label = Unknown()

        return label

    def _merge(self, annotations):

        # annotations[chunk_mid_time] = annotation
        # annotations is a dictionary indexed by chunk middle time
        # it should contains all annotations for one (uri, modality) pair

        # this will be initialized
        # with values taken from the first annotation
        uri = None
        modality = None

        # this is meant to store all hypotheses
        # for all available tracks
        # hypotheses[segment, track] = list of hypotheses
        hypotheses = {}

        # loop on all available annotations
        for mid_time in annotations:

            annotation = annotations[mid_time]

            # set uri and modality with values taken
            # from the first encountered annotation
            if uri is None:
                uri = annotation.uri
                modality = annotation.modality

            # build hypotheses dictionary
            for s, t, l in annotation.itertracks(label=True):

                # in case it's the first time we encounter this track
                # make sure its hypotheses dictionary is initialized
                if (s, t) not in hypotheses:
                    hypotheses[s, t] = {}

                hypotheses[s, t][mid_time] = l

        # do the actual merging based on all available hypotheses
        annotation = Annotation(uri=uri, modality=modality)
        for (segment, track), H in hypotheses.iteritems():
            annotation[segment, track] = self._decide(segment, track, H)

        return annotation

    def __call__(
        self,
        pig,
        threads=None, mip_gap=None, time_limit=None,
        verbose=False, **kwargs
    ):

        # this is used to store results of optimization
        # on each subgraph. dict is indexed by middle time
        # sub_annotations[chunk_mid_time] = { uri, modality ==> annotation }
        sub_annotations = {}

        # process subgraph by subgraph
        # g is subgraph, middle time
        for g, mid_time in self._chunk(pig, 3):

            self.set_problem(g)
            self.set_constraints(g)
            self.set_objective(g, g.get_similarity, **kwargs)
            solution = self.solve(
                threads=threads,
                mip_gap=mip_gap,
                time_limit=time_limit,
                verbose=verbose)
            clusters = self.get_clusters(g, solution)
            sub_annotations[mid_time] = self.get_annotations(g, clusters)

        # set of (uri, modality) pairs
        uri_modality_pairs = set([
            (u, m)
            for t, a in sub_annotations.iteritems()
            for u, m in a
        ])

        # annotations[uri, modality] = final (merged) annotation
        annotations = {}

        for uri, modality in uri_modality_pairs:

            # gather all hypotheses for current u/m pair
            # hypotheses[chunk_mid_time] = annotation for current u/m pair

            hypotheses = {}
            for chunk_mid_time, A in sub_annotations.iteritems():
                if (uri, modality) in A:
                    hypotheses[chunk_mid_time] = A[uri, modality]

            # do the actual merging of all hypotheses for current u/m pair
            annotations[uri, modality] = self._merge(hypotheses)

        return annotations
