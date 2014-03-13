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

from hac import HierarchicalAgglomerativeClustering
from model import HACModel
from stop import HACStop
import numpy as np


class SimilarityThresholdStop(HACStop):

    def __init__(self):
        super(SimilarityThresholdStop, self).__init__()

    def initialize(self, threshold=0, **kwargs):
        self.threshold = threshold

    def update(self, merged_clusters, new_cluster, **kwargs):
        pass

    def reached(self, history=None, **kwargs):
        last_iteration = history.iterations[-1]
        return last_iteration.similarity < self.threshold

    def finalize(self, history=None, **kwargs):
        n = len(history.iterations)
        return history[n-1]


class HACLinkageModel(HACModel):

    def __init__(self):
        super(HACLinkageModel, self).__init__()

    def get_model(self, cluster, **kwargs):
        return tuple([cluster])

    def merge_models(self, clusters, models=None, **kwargs):
        if models is None:
            raise ValueError('')

        new_model = []
        for cluster in clusters:
            other_model = models[cluster]
            new_model.extend(other_model)
        return tuple(new_model)

    def is_symmetric(self):
        return False


class CompleteLinkageModel(HACLinkageModel):

    def get_similarity(
        self, cluster1, cluster2, models=None, feature=None, **kwargs
    ):

        if models is None:
            raise ValueError('')

        if feature is None:
            raise ValueError('')

        model1 = models[cluster1]
        model2 = models[cluster2]
        return np.min(
            feature.subset(
                rows=set(model1), columns=set(model2)
            ).df.values
        )


class AverageLinkageModel(HACLinkageModel):

    def get_similarity(
        self, cluster1, cluster2, models=None, feature=None, **kwargs
    ):

        if models is None:
            raise ValueError('')

        if feature is None:
            raise ValueError('')

        model1 = models[cluster1]
        model2 = models[cluster2]
        return np.mean(
            feature.subset(
                rows=set(model1), columns=set(model2)
            ).df.values
        )


class SingleLinkageModel(HACLinkageModel):

    def get_similarity(
        self, cluster1, cluster2, models=None, feature=None, **kwargs
    ):

        if models is None:
            raise ValueError('')

        if feature is None:
            raise ValueError('')

        model1 = models[cluster1]
        model2 = models[cluster2]
        return np.max(
            feature.subset(
                rows=set(model1), columns=set(model2)
            ).df.values
        )


class CompleteLinkageClustering(HierarchicalAgglomerativeClustering):

    def __init__(self, threshold=None):
        model = CompleteLinkageModel()
        stop = SimilarityThresholdStop(threshold=threshold)
        super(CompleteLinkageClustering, self).__init__(model=model, stop=stop)

    def __call__(self, annotation, matrix):
        """
        annotation : Annotation
        matrix : LabelMatrix
            Label similarity matrix
        """
        return super(CompleteLinkageClustering, self).__call__(
            annotation, feature=matrix)


class AverageLinkageClustering(HierarchicalAgglomerativeClustering):

    def __init__(self, threshold=None):
        model = AverageLinkageModel()
        stop = SimilarityThresholdStop(threshold=threshold)
        super(AverageLinkageClustering, self).__init__(model=model, stop=stop)

    def __call__(self, annotation, matrix):
        return super(AverageLinkageClustering, self).__call__(
            annotation, feature=matrix)


class SingleLinkageClustering(HierarchicalAgglomerativeClustering):

    def __init__(self, threshold=None):
        model = SingleLinkageModel()
        stop = SimilarityThresholdStop(threshold=threshold)
        super(SingleLinkageClustering, self).__init__(model=model, stop=stop)

    def __call__(self, annotation, matrix):
        return super(SingleLinkageClustering, self).__call__(
            annotation, feature=matrix)
