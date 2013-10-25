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

import numpy as np
import sklearn
from sklearn.mixture import GMM
from joblib import Parallel, delayed
from pyannote import Scores
import itertools


class UBM(GMM):

    def adapt(self, X, params='m'):
        """
        Create a new GMM adapted from UBM with the
        expectation-maximization algorithm

        Parameters
        ----------
        X : array_like, shape (n, n_features)
            List of n_features-dimensional data points.  Each row
            corresponds to a single data point.
        params : string, optional
            Controls which parameters are updated in the adaptation
            process.  Can contain any combination of 'w' for weights,
           'm' for means, and 'c' for covars.  Defaults to 'm'.

        Returns
        -------
        gmm : GMM
            Adapted UBM

        """

        # copy UBM parameters
        gmm = sklearn.clone(self)

        # DO NOT re-initialize weights, means and covariances
        gmm.init_params = ""
        gmm.weights_ = self.weights_
        gmm.means_ = self.means_
        gmm.covars_ = self.covars_
        gmm.converged_ = self.converged_

        # only adapt requested parameters
        gmm.params = params
        gmm.fit(X)

        return gmm


def _get_adapted_gmm(ubm, X, params):
    return ubm.adapt(X, params=params)


class GMMUBM(object):
    """

    Parameters
    ----------
    ubm : UBM, optional
    n_components : int, optional
    covariance_type : str, optional
    n_jobs : int, optional
        Number of parallel jobs for GMM adaptation
        (default is one core). Use -1 for all cores.
    params : string, optional
        Controls which parameters are updated in the adaptation
        process.  Can contain any combination of 'w' for weights,
       'm' for means, and 'c' for covars.  Defaults to 'm'.
    """

    def __init__(
        self, ubm=None, n_components=256, covariance_type='diag',
        params='m', n_jobs=1
    ):
        super(GMMUBM, self).__init__()

        if ubm is None:
            self.ubm = UBM(
                n_components=n_components, covariance_type=covariance_type)
        else:
            self.ubm = ubm

        self.params = params
        self.n_jobs = n_jobs

    def fit(self, annotation_and_feature_iterable):
        """
        """

        classes = set()

        # x[k] contains a list of features for class k
        x = {}

        # gather training data
        for a, f in annotation_and_feature_iterable:

            # add previously unseen classes
            classes.update(a.labels())

            # gather features for each class
            for k in classes:
                if k not in x:
                    x[k] = []
                x[k].append(f.crop(a.label_coverage(k)))

        classes = sorted(classes)

        for k in classes:
            x[k] = np.vstack(x[k])
            print k, x[k].shape

        if not self.ubm.converged_:
            # gather balanced training data
            # rule of thumb:
            # 200 samples by gaussians equally split between all classes
            # X = ...
            # traing UBM
            X = np.vstack(x.itervalues())
            n = self.ubm.n_components * 200
            N = len(X)
            step = N / float(n)
            self.ubm.fit(X[::step])

        # adapt UBM for to each class
        if self.n_jobs == 1:
            gmms = [
                _get_adapted_gmm(self.ubm, x[k], self.params)
                for k in classes
            ]
        else:
            gmms = Parallel(n_jobs=self.n_jobs, verbose=5)(
                delayed(_get_adapted_gmm)(self.ubm, x[k], self.params)
                for k in classes
            )

        self.gmms = {k: gmm for k, gmm in itertools.izip(classes, gmms)}

        return self

    def scores(self, annotation, features):

        s = Scores(uri=annotation.uri, modality=annotation.modality)

        # UBM log-likelihood
        ubm_ll = self.ubm.score(features.data)

        for k, gmm in self.gmms.iteritems():

            gmm_ll = gmm.score(features.data)
            llr = gmm_ll - ubm_ll

            for segment, track in annotation.itertracks():
                i0, n = features.sliding_window.segmentToRange(segment)
                s[segment, track, k] = np.mean(llr[i0:i0+n])

        return s
