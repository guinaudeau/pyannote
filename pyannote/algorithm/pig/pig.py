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

import networkx as nx
from vertex import InstanceVertex, IdentityVertex

PROBABILITY = 'probability'
PROBABILITY_ONE = 1
PROBABILITY_ZERO = 0


class PersonInstanceGraph(nx.Graph):
    """Person Instance Graph"""

    def __init__(self):
        super(PersonInstanceGraph, self).__init__()

    def add_annotation(self, annotation,
                       instance_vertex=False, identity_vertex=False,
                       identification_edge=False, cooccurrence_edge=False):
        """Add `annotation` to graph

        Parameters
        ----------
        annotation : `Annotation`
            Annotation to be added to the graph.
        instance_vertex : bool, optional
            Set `instance_vertex` to True to add one instance vertex
            per track in `annotation`. Default is False.
        identity_vertex : bool, optional
            Set `identity_vertex` to True to add one identity vertex
            per label in `annotation`. Default is False.
        identification_edge : bool, optional
            Set `identification_edge` to True to add p=1 edges between
            each instance vertex (track) and their corresponding identity
            vertex (label). Default is False.
        cooccurrence_edge : bool, optional
            Set `cooccurrence_edge` to True to add p=0 edges between instance
            vertices corresponding to cooccurring tracks. Default is False.

        Notes
        -----
        Setting `cooccurrence_edge` to True implies setting `instance_vertex`
        to True (no warning is raised).
        Setting `identification_edge` to True implies setting both
        `instance_vertex` and `identity_vertex` to True.

        """

        uri = annotation.uri
        modality = annotation.modality

        if identification_edge:
            instance_vertex = True
            identity_vertex = True

        if cooccurrence_edge:
            instance_vertex = True

        # Add identity vertices (one par label)
        if identity_vertex:

            for label in annotation.labels():
                i = IdentityVertex(identity=label)
                self.add_node(i)

        # Add instance vertices (one per track)
        if instance_vertex:

            for segment, track in annotation.itertracks():
                v = InstanceVertex(
                    segment=segment, track=track, modality=modality, uri=uri
                )
                self.add_node(v)

        # Add identification edges (one per (track, label) pair)
        if identification_edge:

            for segment, track, label in annotation.itertracks(label=True):

                v = InstanceVertex(
                    segment=segment, track=track, modality=modality, uri=uri
                )
                i = IdentityVertex(identity=label)

                self.add_edge(v, i, {PROBABILITY: PROBABILITY_ONE})

        # Add cooccurrence edges (one per pair of cooccurring tracks)
        if cooccurrence_edge:

            for segment, track in annotation.itertracks():

                v = InstanceVertex(
                    segment=segment, track=track, modality=modality, uri=uri
                )

                # Loop on cooccurring tracks
                for s, t in annotation.crop(segment, mode='loose').itertracks():

                    w = InstanceVertex(
                        segment=s, track=t, modality=modality, uri=uri
                    )

                    # Prevent loop edges from being added to the graph
                    # (even though every track does cooccur with itself...)
                    if v != w:
                        self.add_edge(v, w, {PROBABILITY: PROBABILITY_ZERO})

        return self

    def add_scores(self, scores):
        """Add `scores` to graph

        Parameters
        ----------
        scores : `Scores`
            Identification scores to be added to the graph.

        """

        uri = scores.uri
        modality = scores.modality

        for segment, track, label, probability in scores.itervalues():

            # Make sure the score is actually a probabiliy
            assert 0 <= probability and probability <= 1

            v = InstanceVertex(
                segment=segment, track=track, modality=modality, uri=uri
            )

            i = IdentityVertex(identity=label)

            # Add the edge between current (track, label) pair
            self.add_edge(v, i, {PROBABILITY: probability})

        return self

    def add_matrix(self, matrix):
        """Add track similarity matrix

        Parameters
        ----------
        matrix : `LabelMatrix`
            Affinity matrix indexed by instance vertices
        """

        # Make sure rows are instance vertices
        assert all(
            [isinstance(v, InstanceVertex) for v in matrix.get_rows()]
        )
        # Make sure columns are instance vertices
        assert all(
            [isinstance(w, InstanceVertex) for w in matrix.get_columns()]
        )

        # Add affinity edges between instance vertices
        for v, w, probability in matrix.itervalues():
            self.add_edge(v, w, {PROBABILITY: probability})

        return self
