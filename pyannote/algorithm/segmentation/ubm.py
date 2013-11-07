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
from pyannote import Timeline, Annotation, Scores, Unknown
from pyannote.stats.llr import logsumexp
import itertools


class LBG_GMM(GMM):
    """

    Parameters
    ----------
    n_components : int, optional
        Number of mixture components. Defaults to 1.

    covariance_type : string, optional
        String describing the type of covariance parameters to
        use.  Must be one of 'spherical', 'tied', 'diag', 'full'.
        Defaults to 'diag' (the only one supported for now...)

    random_state: RandomState or an int seed (0 by default)
        A random number generator instance

    min_covar : float, optional
        Floor on the diagonal of the covariance matrix to prevent
        overfitting.  Defaults to 1e-3.

    thresh : float, optional
        Convergence threshold. Defaults to 1e-2.

    n_iter : int, optional
        Number of EM iterations per split. Defaults to 10.

    sampling : int, optional
        Reduce the number of samples used for the initialization steps to
        `sampling` samples per component. A few hundreds samples per component
        should be a reasonable rule of thumb.
        The final estimation steps always use the whole sample set.

    disturb : float, optional
        Weight applied to variance when splitting Gaussians. Defaults to 0.05.
        mu+ = mu + disturb * sqrt(var)
        mu- = mu - disturb * sqrt(var)

    Attributes
    ----------
    `weights_` : array, shape (`n_components`,)
        This attribute stores the mixing weights for each mixture component.

    `means_` : array, shape (`n_components`, `n_features`)
        Mean parameters for each mixture component.

    `covars_` : array
        Covariance parameters for each mixture component.  The shape
        depends on `covariance_type`::

            (n_components, n_features)             if 'spherical',
            (n_features, n_features)               if 'tied',
            (n_components, n_features)             if 'diag',
            (n_components, n_features, n_features) if 'full'

    `converged_` : bool
        True when convergence was reached in fit(), False otherwise.

    """

    def __init__(self, n_components=1, covariance_type='diag',
                 random_state=None, thresh=1e-2, min_covar=1e-3,
                 n_iter=10, disturb=0.05, sampling=0):

        if covariance_type != 'diag':
            raise NotImplementedError(
                'Only diagonal covariances are supported.')

        super(LBG_GMM, self).__init__(
            n_components=n_components, covariance_type=covariance_type,
            random_state=random_state, thresh=thresh, min_covar=min_covar,
            n_iter=n_iter, n_init=1, params='wmc', init_params='')

        self.disturb = disturb
        self.sampling = sampling

    def _subsample(self, X, n_components):
        """Down-sample data points according to current number of components

        Successive calls will return different sample sets, based on the
        internal _counter which is incremented after each call.

        Parameters
        ----------
        X : array_like, shape (N, n_features)
            List of n_features-dimensional data points.  Each row
            corresponds to a single data point.

        Returns
        -------
        x : array_like, shape (n < N, n_features)
            Subset of X, with n close to n_components x sampling
        """

        x = X
        step = len(X) / (self.sampling * n_components)
        if step >= 2:
            x = X[(self._counter % step)::step]
            self._counter += 1
        return x

    def _split(self, gmm, n_components):
        """Split gaussians and return new mixture.

        Parameters
        ----------
        gmm : sklearn.mixture.GMM
        n_components : int
            Number of components in new mixture with the following constraint:
            gmm.n_components < n_components <= 2 x gmm.n_components

        Returns
        -------
        new_gmm : sklearn.mixture.GMM
            New mixture with n_components components.

        """

        # TODO: sort gmm components in importance order so that the most
        # important ones are the one actually split...

        new_gmm = GMM(n_components=n_components,
                      covariance_type=self.covariance_type,
                      random_state=self.random_state,
                      thresh=self.thresh,
                      min_covar=self.min_covar,
                      n_iter=1,
                      params=self.params,
                      n_init=self.n_init,
                      init_params='')

        # number of new components to be added
        k = n_components - gmm.n_components

        # split weights
        new_gmm.weights_[:k] = gmm.weights_[:k] / 2
        new_gmm.weights_[k:2*k] = gmm.weights_[:k] / 2

        # initialize means_ with new number of components
        shape = list(gmm.means_.shape)
        shape[0] = n_components
        new_gmm.means_ = np.zeros(shape, dtype=gmm.means_.dtype)
        # TODO: add support for other covariance_type
        # TODO: for now it only supports 'diag'
        noise = self.disturb * np.sqrt(gmm.covars_[:k, :])
        new_gmm.means_[:k, :] = gmm.means_[:k, :] + noise
        new_gmm.means_[k:2*k, :] = gmm.means_[:k, :] - noise

        # initialize covars_ with new number of components
        shape = list(gmm.covars_.shape)
        shape[0] = n_components
        new_gmm.covars_ = np.zeros(shape, dtype=gmm.covars_.dtype)
        # TODO: add support for other covariance_type
        # TODO: for now it only supports 'diag'
        new_gmm.covars_[:k, :] = gmm.covars_[:k, :]
        new_gmm.covars_[k:2*k, :] = gmm.covars_[:k, :]

        # copy remaining unsplit gaussians
        if k < gmm.n_components:
            new_gmm.weights_[2*k:] = gmm.weights_[k:]
            new_gmm.means_[2*k:, :] = gmm.means_[k:, :]
            new_gmm.covars_[2*k:, :] = gmm.covars_[k:, :]

        return new_gmm

    def fit(self, X):
        """Estimate model parameters with LBG initialization and
        the expectation-maximization algorithm.

        Parameters
        ----------
        X : array_like, shape (n, n_features)
            List of n_features-dimensional data points.  Each row
            corresponds to a single data point.
        """

        self._counter = 0

        # init with one gaussian
        gmm = GMM(n_components=1, covariance_type=self.covariance_type,
                  random_state=self.random_state, thresh=self.thresh,
                  min_covar=self.min_covar, n_iter=1,
                  n_init=1, params=self.params,
                  init_params='')

        while gmm.n_components < self.n_components:

            # fit GMM on a rolling subset of training data
            if self.sampling > 0:
                for i in range(self.n_iter):
                    x = self._subsample(X, gmm.n_components)
                    gmm.fit(x)
            else:
                gmm.n_iter = self.n_iter
                gmm.fit(X)

            # increase number of components (x 2)
            n_components = min(self.n_components, 2*gmm.n_components)
            gmm = self._split(gmm, n_components)

        # final fit with all the data
        gmm.n_iter = self.n_iter
        gmm.fit(X)

        # copy fitted parameters
        self.weights_ = gmm.weights_
        self.means_ = gmm.means_
        self.covars_ = gmm.covars_
        self.converged_ = gmm.converged_

        return self

    def adapt(self, X, params='m', n_iter=10):
        """Adapt mixture to new data using the EM algorithm

        This is an implementation of the Universal Background Model adaptation
        technique usually applied in the speaker identification community.

        Parameters
        ----------
        X : array_like, shape (n, n_features)
            List of n_features-dimensional data points.  Each row
            corresponds to a single data point.
        params : string, optional
            Controls which parameters are adapted.  Can contain any combination
            of 'w' for weights, 'm' for means, and 'c' for covars.
            Defaults to 'm'.
        n_iter : int, optional
            Number of EM iterations to perform.

        Returns
        -------
        gmm : GMM
            Adapted UBM

        """

        # copy UBM parameters
        gmm = sklearn.clone(self)
        gmm = GMM(
            n_components=self.n_components,
            covariance_type=self.covariance_type,
            params=params, n_iter=10,  # only adapt requested parameters
            n_init=1, init_params='',  # initialize with UBM attributes
            random_state=self.random_state,
            thresh=self.thresh, min_covar=self.min_covar,
        )

        # initialize with UBM attributes
        gmm.weights_ = self.weights_
        gmm.means_ = self.means_
        gmm.covars_ = self.covars_

        # adaptation
        gmm.fit(X)

        return gmm


def _get_adapted_gmm(ubm, X, params):
    return ubm.adapt(X, params=params)


class GMMUBM(object):
    """GMM/UBM speaker identification

    Parameters
    ----------
    ubm : LBG_GMM
        Universal Background Model
    targets : iterable, optional
        When provided, targets contain the list of target to be recognized.
        All other labels encountered during training are considered as unknown.
    params : string, optional
        Controls which parameters are adapted.  Can contain any combination
        of 'w' for weights, 'm' for means, and 'c' for covars.
        Defaults to 'm'.
    n_iter : int, optional
        Number of EM iterations to perform during adaptation.
    n_jobs : int, optional
        Number of parallel jobs for GMM adaptation
        (default is one core). Use -1 for all cores.
    """

    def __init__(
        self, ubm, targets=None, params='m', n_iter=10, n_jobs=1
    ):

        super(GMMUBM, self).__init__()

        self.ubm = ubm
        self.params = params
        self.n_iter = n_iter
        self.n_jobs = n_jobs
        self.targets = targets

    def fit(self, annotation_and_feature_iterable):
        """

        Parameters
        ----------
        annotation_and_feature_iterable :
            Annotation may contain `Unknown` instance labels.
        """

        # == build training sets for each class

        # set of classes
        classes = set()

        # list of features for each class
        # k --> [ features, features, features, ]
        x = {}

        # loop over training set
        for a, f in annotation_and_feature_iterable:

            # add previously unseen classes
            classes.update(a.labels())

            # gather features for each class
            for k in classes:

                # initialize list of features
                # if class `k` was not seen before
                if k not in x:
                    x[k] = []

                # if class `k` is represented in current annotation
                # and corresponding features
                coverage = a.label_coverage(k)
                if coverage:
                    x[k].append(f.crop(coverage))

        # concatenate features for each class
        for k in classes:
            x[k] = np.vstack(x[k])

        # == estimate priors

        if self.targets is None:
            self.targets_ = sorted([
                k for k in classes if not isinstance(k, Unknown)])
        else:
            self.targets_ = sorted(
                set(classes) & set(self.targets))

        self.priors_ = {}
        total = np.sum([len(x[k]) for k in classes])
        unknown = 0
        for k in classes:
            if k in self.targets_:
                self.priors_[k] = len(x[k]) / float(total)
            else:
                unknown += len(x[k])
        self.priors_[Unknown] = unknown / float(total)

        # == adapt UBM to training set for each class

        # order classes for later use

        # sequential adaptation
        if self.n_jobs == 1:
            gmms = [
                self.ubm.adapt(x[k], params=self.params, n_iter=self.n_iter)
                for k in self.targets_
            ]

        # parallel adaptation
        else:
            gmms = Parallel(n_jobs=self.n_jobs, verbose=5)(
                delayed(_get_adapted_gmm)(self.ubm, x[k], self.params)
                for k in self.targets_
            )

        # save adapted GMMs to gmms_ attribute
        self.gmms_ = {k: gmm for k, gmm in itertools.izip(self.targets_, gmms)}

        return self

    def scores(self, segmentation, features):
        """Compute GMM/UBM log-likelihood ratios

        Parameters
        ----------
        segmentation : Timeline or Annotation
            Pre-computed segmentation.
        features : pyannote.SlidingWindowFeature
            Pre-computed features.

        Returns
        -------
        scores : pyannote.Scores
            For each (segment, track) in `segmentation`, `scores` provides
            the average GMM/UBM log-likelihood ratio for each class.

        """

        # replace input timeline by annotation with
        # one track per segment and one label per track
        if isinstance(segmentation, Timeline):
            scores = Scores(uri=segmentation.uri)
            _segmentation = Annotation(uri=segmentation.uri, modality=None)
            for s in segmentation:
                _segmentation[s, '_'] = Unknown()
            segmentation = _segmentation

        # create empty scores to hold all scores
        scores = Scores(uri=segmentation.uri, modality=segmentation.modality)

        # UBM log-likelihood
        ubm_ll = self.ubm.score(features.data)

        # TODO: restriction to top-scoring UBM gaussians

        # compute GMM/UBM log-likelihood ratio for each class
        for k in self.targets_:

            gmm = self.gmms_[k]

            # compute log-likelihood for all data points
            # even if they do not correspond to any track
            # TODO: would it really be faster to focus only on track features?
            gmm_ll = gmm.score(features.data)

            # compute log-likelihood ratio
            llr = gmm_ll - ubm_ll

            # TODO: segment-wise or cluster-wise scoring

            # average log-likelihood ratio over the duration of each track
            for segment, track in segmentation.itertracks():

                i0, n = features.sliding_window.segmentToRange(segment)
                scores[segment, track, k] = np.mean(llr[i0:i0+n])

        return scores

    def _llr2posterior(self, llr, priors, unknown_prior):
        denominator = (
            unknown_prior +
            np.exp(logsumexp(llr, b=priors, axis=1))
        )
        posteriors = ((priors * np.exp(llr)).T / denominator).T
        return posteriors

    def predict_proba(self, annotation, features, equal_priors=False):
        """Compute posterior probabilities

        Parameters
        ----------
        annotation : pyannote.Annotation
            Pre-computed segmentation.
        features : pyannote.SlidingWindowFeature
            Pre-computed features.
        equal_priors : bool, optional
            If True, set equal priors to targets.
            Defaults to False (i.e. use learned priors)

        Returns
        -------
        probs : pyannote.Scores
            For each (segment, track) in `annotation`, `scores` provides
            the posterior probability for each class.

        """

        # get raw log-likelihood ratio
        scores = self.scores(annotation, features)

        unknown_prior = self.priors_[Unknown]

        # get ordered target priors
        if equal_priors:
            n = len(self.targets_)
            priors = (1-unknown_prior) * np.ones(n) / n
        else:
            priors = np.array([self.priors_[t] for t in self.targets_])

        # compute posterior from LLR directly on the internal numpy array
        func = lambda llr: self._llr2posterior(llr, priors, unknown_prior)
        return scores.apply(func)

    def predict(self, annotation, features, equal_priors=False):
        """Predict label of each track (open-set speaker identification)

        Parameters
        ----------
        annotation : pyannote.Annotation
            Pre-computed segmentation.
        features : pyannote.SlidingWindowFeature
            Pre-computed features.
        equal_priors : bool, optional
            If True, set equal priors to targets.
            Defaults to False (i.e. use learned priors)

        Returns
        -------
        prediction : pyannote.Annotation
            Copy of `annotation` with predicted labels (or Unknown).

        """

        probs = self.predict_proba(
            annotation, features, equal_priors=equal_priors)
        return probs.to_annotation(posterior=True)
