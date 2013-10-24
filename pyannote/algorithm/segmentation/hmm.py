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

import numpy as np
from sklearn.mixture import GMM
from sklearn.hmm import GMMHMM
from pyannote import Segment, Annotation
from joblib import Parallel, delayed


# this function is defined here in order to be able
# to use it later with joblib.Parallel
def _gmm_helper(data, n_components, covariance_type):
    """Estimate Gaussian Mixture Model

    Parameters
    ----------
    data : (N, D) numpy array
        Array of N feature vectors of dimension D
    n_components : int
        Number of gaussians
    covariance_type : {'diag', 'full'}
        Type of gaussian covariance matrices

    Returns
    -------
    gmm : `sklearn.mixture.GMM`
        Gaussian mixture model estimated from `data`
    """

    gmm = GMM(
        n_components=n_components,
        covariance_type=covariance_type,
        params='wmc')
    gmm.fit(data)
    return gmm


class HMMSegmentation(object):

    """HMM-based segmentation with Viterbi decoding

    Parameters
    ----------
    n_components : int
        Number of gaussians per HMM state (default is 1).
    covariance_type : {'diag', 'full'}
        Type of gaussian covariance matrices
    n_jobs : int
        Number of parallel jobs for GMM estimation
        (default is all available cores)

    """

    def __init__(self, n_components=1, covariance_type='diag', n_jobs=1):

        super(HMMSegmentation, self).__init__()
        self.n_components = n_components
        self.covariance_type = covariance_type
        self.n_jobs = n_jobs

    def fit(self, annotation_and_feature_iterable):
        """Train HMM segmentation

        The resulting HMM will contain one state per labels in training set.

        Parameters
        ----------
        annotation_and_feature_iterable : iterable -> [(a1, f1), (a2, f2), ...]
            Yield a list of (a, f) pairs where `a` is an `Annotation` whose
            labels will be HMM states and `f` is the associated `Features`.

        """

        K = set()

        # x[k] contains a list of features for class k
        x = {}

        # X contains list of utterances
        X = []

        # gather training data
        for a, f in annotation_and_feature_iterable:

            # keep track of utterance
            X.append(f.data)

            # add previously unseen classes
            K.update(a.labels())

            # gather features for each class
            for k in K:
                if k not in x:
                    x[k] = []
                x[k].append(f.crop(a.label_coverage(k)))

        # keep track of HMM states order
        self.states = sorted(K)

        if self.n_jobs == 1:
            self.gmms = [_gmm_helper(
                np.vstack(x[k]), self.n_components, self.covariance_type)
                for k in self.states]
        else:
            self.gmms = Parallel(n_jobs=self.n_jobs, verbose=5)(
                delayed(_gmm_helper)(
                    np.vstack(x[k]), self.n_components, self.covariance_type
                ) for k in self.states
            )

        self.hmm = GMMHMM(
            n_components=len(self.states), gmms=self.gmms,
            init_params='st', params='st'
        )
        self.hmm.fit(X)

    def apply(self, features):

        # predict state sequences
        sequence = self.hmm.predict(features.data)

        # start initial segment
        start = 0
        label = self.states[sequence[0]]

        segmentation = Annotation()

        for i, d in enumerate(np.diff(sequence)):

            if d == 0:
                continue

            # end of current segment
            end = i
            segment = features.sliding_window.rangeToSegment(start, end-start)
            segmentation[segment, '_'] = label

            # start of a new segment
            label = self.states[sequence[i+1]]
            start = end

        segment = Segment(segment.end, features.getExtent().end)
        segmentation[segment, '_'] = label

        return segmentation
