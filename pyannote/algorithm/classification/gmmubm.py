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
import logging

import numpy as np
import sklearn
from sklearn.mixture import GMM

from pyannote import Timeline, Annotation, Scores, Unknown
from pyannote.stats.llr import logsumexp
from pyannote.stats.lbg import LBG


class ClassificationGMMUBM(object):
    """GMM/UBM speaker identification

    This is an implementation of the Universal Background Model adaptation
    technique usually applied in the speaker identification community.


    == Universal Background Model ==

    ubm : GMM, optional
        Pre-computed Universal Background Model.

    n_components : int, optional
        Number of mixture components in UBM. Defaults to 1.

    covariance_type : string, optional
        String describing the type of covariance parameters to
        use.  Must be one of 'spherical', 'tied', 'diag', 'full'.
        Defaults to 'diag' (the only one supported for now...)

    n_iter : int, optional
        Number of EM iterations to perform during training/adaptation.
        Defaults to 10.

    random_state: RandomState or an int seed (0 by default)
        A random number generator instance

    min_covar : float, optional
        Floor on the diagonal of the covariance matrix to prevent
        overfitting.  Defaults to 1e-3.

    thresh : float, optional
        Convergence threshold. Defaults to 1e-2.

    sampling : int, optional
        Reduce the number of samples used for the initialization steps to
        `sampling` samples per component. A few hundreds samples per component
        should be a reasonable rule of thumb.
        The final estimation steps always use the whole sample set.

    disturb : float, optional
        Weight applied to variance when splitting Gaussians. Defaults to 0.05.
        mu+ = mu + disturb * sqrt(var)
        mu- = mu - disturb * sqrt(var)

    balance : bool, optional
        If True, try to balance target durations used for training of the UBM.
        Defaults to False (i.e. use all available data).

    == Adaptation ==

    targets : iterable, optional
        When provided, targets contain the list of target to be recognized.
        All other labels encountered during training are considered as unknown.

    gmms : dict, optional
        Pre-computed target models.

    params : string, optional
        Controls which parameters are adapted.  Can contain any combination
        of 'w' for weights, 'm' for means, and 'c' for covars.
        Defaults to 'm'.

    n_iter : int, optional
        Number of EM iterations to perform during training/adaptation.
        Defaults to 10.

    n_jobs : int, optional
        Number of parallel jobs for GMM adaptation
        (default is one core). Use -1 for all cores.

    == Scoring ==

    equal_priors : bool, optional
        When True, use equal priors. Defaults to False (learned priors).

    open_set : bool, optional
        When True, perform open-set classification
        Defaults to False (close-set classification).

    """

    def __init__(
        self,
        ubm=None,
        n_components=1, covariance_type='diag',
        random_state=None, thresh=1e-2, min_covar=1e-3,
        n_iter=10, disturb=0.05, sampling=0, balance=False,
        targets=None, gmm=None,
        params='m',
        equal_priors=False, open_set=False,
        n_jobs=1
    ):

        super(ClassificationGMMUBM, self).__init__()

        # pre-computed UBM
        self.ubm = ubm

        # UBM training
        self.n_components = n_components
        self.covariance_type = covariance_type
        self.random_state = random_state
        self.thresh = thresh
        self.min_covar = min_covar
        self.n_iter = n_iter
        self.disturb = disturb
        self.sampling = sampling
        self.balance = balance

        self.targets = targets

        self.gmm = gmm
        if self.gmm is None:
            self.gmm = {}

        self.params = params
        self.n_jobs = n_jobs

        # scoring
        self.equal_priors = equal_priors
        self.open_set = open_set

    def adapt(self, X):
        """Adapt UBM to new data using the EM algorithm

        Parameters
        ----------
        X : array_like, shape (n, n_features)
            List of n_features-dimensional data points.  Each row
            corresponds to a single data point.

        Returns
        -------
        gmm : GMM
            Adapted UBM

        """

        # copy UBM structure and parameters
        gmm = sklearn.clone(self.ubm)
        gmm = GMM(
            params=self.params,  # only adapt requested parameters
            n_iter=self.n_iter,
            n_init=1,
            init_params=''       # initialize with UBM attributes
        )

        # initialize with UBM attributes
        gmm.weights_ = self.ubm.weights_
        gmm.means_ = self.ubm.means_
        gmm.covars_ = self.ubm.covars_

        # adaptation
        gmm.fit(X)

        return gmm

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

    def _get_chart(self, reference):
        """Get target chart {label: duration, ..., Unknown: duration}

        Assumes `targets` attribute is already set.

        Parameters
        ----------
        reference : `Annotation` iterable

        """

        # accumulate total duration of each label
        chart = {}

        for annotation in reference:
            for label, duration in annotation.chart():

                if label in self.targets:
                    chart[label] = chart.get(label, 0) + duration

                else:
                    chart[Unknown] = chart.get(Unknown, 0) + duration

        return chart

    def _get_ubm(self, reference, features, chart):
        """

        Parameters
        ----------
        reference : `Annotation` iterable
        features : `SlidingWindowFeature` iterable
        chart : {target: duration} dict, optional
            When provided, try to reduce the influence of dominant targets
            during UBM training

        Returns
        -------
        ubm : `sklearn.mixture.GMM`
            Universal Background Model
        """

        if self.balance:
            raise NotImplementedError('target balancing not supported yet.')
            for label, duration in chart.iteritems():
                # reduce weight of dominant labels
                pass

        else:
            # concatenate all available training data
            data = np.vstack([
                f.crop(r.get_timeline().coverage())  # use labeled regions only
                for r, f in itertools.izip(reference, features)
            ])

        lbg = LBG(
            n_components=self.n_components,
            covariance_type=self.covariance_type,
            random_state=self.random_state,
            thresh=self.thresh,
            min_covar=self.min_covar,
            n_iter=self.n_iter,
            disturb=self.disturb,
            sampling=self.sampling)

        ubm = lbg.apply(data)

        return ubm

    def _get_gmm(self, reference, features, target):

        # gather target data
        data = np.vstack([
            f.crop(r.label_coverage(target))  # use target regions only
            for r, f in itertools.izip(reference, features)
        ])

        # adapt UBM to target data
        gmm = self.adapt(data)

        return gmm

    def fit(self, reference, features):
        """

        Parameters
        ----------
        reference : `Annotation` generator
            Generates annotations whose labels will be GMM/UBM targets
        features : `Feature` generator
            Generates features synchronized with `reference`
        """

        # gather training data
        reference = list(reference)
        features = list(features)

        # if needed, gather target list
        if self.targets is None:
            self.targets = self._get_targets(reference)

        # target chart {label: duration, ..., Unknown: duration}
        chart = self._get_chart(reference)

        # target priors
        total = np.sum(chart.values())
        self.priors = {
            label: duration/total for label, duration in chart.iteritems()
        }

        # if needed, train UBM
        if self.ubm is None:
            logging.info('Training UBM')
            self.ubm = self._get_ubm(reference, features, chart=chart)

        # learn target model from training data
        for target in self.targets:
            if target in self.gmm:
                pass
            else:
                logging.info('Adapting UBM to target %s' % str(target))
                self.gmm[target] = self._get_gmm(reference, features, target)

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
        for target in self.targets:

            gmm = self.gmm[target]

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
                # TODO: factorize mean() by h-stacking llr
                scores[segment, track, target] = np.mean(llr[i0:i0+n])

        return scores

    def _llr2posterior(self, llr, priors, unknown_prior):
        denominator = (
            unknown_prior +
            np.exp(logsumexp(llr, b=priors, axis=1))
        )
        posteriors = ((priors * np.exp(llr)).T / denominator).T
        return posteriors

    def predict_proba(self, segmentation, features):
        """Compute posterior probabilities

        Parameters
        ----------
        segmentation : pyannote.Annotation
            Pre-computed segmentation.
        features : pyannote.SlidingWindowFeature
            Pre-computed features.

        Returns
        -------
        probs : pyannote.Scores
            For each (segment, track) in `segmentation`, `scores` provides
            the posterior probability for each class.

        """

        # get raw log-likelihood ratio
        scores = self.scores(segmentation, features)

        # reduce Unknown prior to 0. in case of close-set classification
        unknown_prior = self.priors.get(Unknown, 0.)
        if self.open_set is False:
            unknown_prior = 0.

        # number of known targets
        n_targets = len(self.targets)

        if self.equal_priors:

            # equally distribute known prior between known targets
            priors = (1-unknown_prior) * np.ones(n_targets) / n_targets

        else:

            # ordered known target priors
            priors = np.array([self.priors[t] for t in self.targets])

            # in case of close-set classification
            # equally distribute unknown prior to known targets
            if self.open_set is False:
                priors = priors + self.priors.get(Unknown, 0.)/n_targets

        # compute posterior from LLR directly on the internal numpy array
        func = lambda llr: self._llr2posterior(llr, priors, unknown_prior)
        return scores.apply(func)

    def predict(self, segmentation, features):
        """Predict label of each track

        Parameters
        ----------
        segmentation : pyannote.Annotation
            Pre-computed segmentation.
        features : pyannote.SlidingWindowFeature
            Pre-computed features.

        Returns
        -------
        prediction : pyannote.Annotation
            Copy of `segmentation` with predicted labels (or Unknown).

        """

        probs = self.predict_proba(segmentation, features)

        if self.open_set:
            # open-set classification returns Unknown
            # when best target score is below unknown prior
            return probs.to_annotation(posterior=True)

        else:
            # close-set classification always returns
            # the target with the best score
            return probs.to_annotation(posterior=False)
