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


import logging
import itertools

import numpy as np
from scipy.ndimage.filters import median_filter
from sklearn.hmm import GMMHMM

from pyannote.stats.lbg import LBG
from pyannote import Segment, Annotation, Unknown

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

    lbg = LBG(
        n_components=n_components,
        covariance_type='diag',
        sampling=1000,
        n_iter=10,
        disturb=0.05
    )

    return lbg.apply(data)


class SegmentationHMM(object):

    """HMM-based segmentation with Viterbi decoding

    Parameters
    ----------
    n_components : int
        Number of gaussians per HMM state (default is 1).
    covariance_type : {'diag', 'full'}
        Type of gaussian covariance matrices
    min_duration : float, optional
        Filter out segments shorter than `min_duration` seconds
    n_jobs : int
        Number of parallel jobs for GMM estimation
        (default is one core)

    """

    def __init__(
        self, n_components=1, covariance_type='diag',
        min_duration=None, n_jobs=1
    ):

        super(SegmentationHMM, self).__init__()
        self.n_components = n_components
        self.covariance_type = covariance_type
        self.n_jobs = n_jobs
        self.min_duration = min_duration
        self.gmm = {}

    def _get_targets(self, reference):
        """Get list of targets from training data

        Parameters
        ----------
        reference : `Annotation` iterable

        Returns
        -------
        targets : list
            Sorted list of 'known' targets

        """
        # empty target set
        targets = set()

        for annotation in reference:
            labels = [
                L for L in annotation.labels()
                if not isinstance(L, Unknown)
            ]
            targets.update(labels)

        return sorted(targets)

    def _get_gmm(self, reference, features, target):

        # gather target data
        data = np.vstack([
            f.crop(r.label_coverage(target))  # use target regions only
            for r, f in itertools.izip(reference, features)
        ])

        lbg = LBG(
            n_components=self.n_components,
            covariance_type=self.covariance_type,
            sampling=1000,
            n_iter=10,
            disturb=0.05
        )

        gmm = lbg.apply(data)

        return gmm

    def fit(self, reference, features):
        """Train HMM segmentation

        The resulting HMM will contain one state per labels in training set.

        Parameters
        ----------
        reference : `Annotation` generator
            Generates annotations whose labels will be HMM states
        features : `Feature` generator
            Generates features synchronized with `reference`
        """

        # gather training data
        reference = list(reference)
        features = list(features)

        # gather target list
        self.targets = self._get_targets(reference)

        # train each state
        for target in self.targets:
            logging.info('Training %s GMM' % str(target))
            self.gmm[target] = self._get_gmm(reference, features, target)

        # train HMM
        logging.info('Training %d-states HMM' % len(self.targets))
        self.hmm = GMMHMM(
            n_components=len(self.targets),
            gmms=[self.gmm[target] for target in self.targets],
            init_params='st', params='st'
        )
        self.hmm.fit([f.data for f in features])

        return self

    def apply(self, features):
        """
        Parameters
        ----------
        features : SlidingWindowFeatures
        """

        # predict state sequences
        sequence = self.hmm.predict(features.data)

        # median filtering to get rid of short segments
        if self.min_duration:

            if len(self.targets) > 2:
                raise NotImplementedError(
                    'min_duration is not supported with more than 2 states.'
                )

            dummy = Segment(0, self.min_duration)
            _, n = features.sliding_window.segmentToRange(dummy)
            sequence = median_filter(sequence, size=2*n+1)

        # start initial segment
        start = 0
        label = self.targets[sequence[0]]

        segmentation = Annotation()

        for i, d in enumerate(np.diff(sequence)):

            if d == 0:
                continue

            # end of current segment
            end = i
            segment = features.sliding_window.rangeToSegment(start, end-start)
            segmentation[segment, '_'] = label

            # start of a new segment
            label = self.targets[sequence[i+1]]
            start = end

        segment = Segment(segment.end, features.getExtent().end)
        segmentation[segment, '_'] = label

        return segmentation
