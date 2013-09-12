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
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LinearRegression


class LLR(object):

    def _get_scores_ratios(self, X, Y, nbins=100):

        positive = X[np.where(Y == 1)]
        negative = X[np.where(Y == 0)]

        # todo: smarter bins (bayesian blocks)
        # see jakevdp.github.io/blog/2012/09/12/dynamic-programming-in-python/
        bins = np.arange(np.min(X), np.max(X), (np.max(X) - np.min(X)) / nbins)

        # histograms
        p, _ = np.histogram(positive, bins=bins, density=True)
        n, _ = np.histogram(negative, bins=bins, density=True)

        scores = .5 * (bins[:-1] + bins[1:])
        ratios = np.log(1. * p / n)

        ok = np.where(np.isfinite(ratios))
        scores = scores[ok]
        ratios = ratios[ok]

        # todo: remove bins based on Doddington's "rule of 30"
        # P, _ = np.histogram(positive, bins=bins, density=False)
        # N, _ = np.histogram(negative, bins=bins, density=False)
        # ok = np.where(np.minimum(P, N) > 30)
        # scores = scores[ok]
        # ratios = ratios[ok]

        return scores, ratios

    def _get_prior(self, X, Y):

        positive = X[np.where(Y == 1)]
        negative = X[np.where(Y == 0)]
        return 1. * len(positive) / (len(positive) + len(negative))

    def toPosteriorProbability(self, scores, prior=None):
        """Get posterior probability given scores

        Parameters
        ----------
        scores : numpy array
            Test scores

        prior : float, optional
            By default, prior is set to the one estimated with .fit()

        Returns
        -------
        posterior : numpy array
            Posterior probability array with same shape as input `scores`

        """

        # Get log-likelihood ratio
        llr = self.toLogLikelihoodRatio(scores)

        # Get prior
        if prior is None:
            prior = self.prior
        priorRatio = (1.-prior) / prior

        # Compute posterior probability
        return 1/(1+priorRatio*np.exp(-llr))


class LLRIsotonicRegression(LLR):
    """Log-likelihood ratio estimation by isotonic regression"""

    def __init__(self):
        super(LLRIsotonicRegression, self).__init__()

    def fit(self, X, Y):

        self.prior = self._get_prior(X, Y)

        scores, ratios = self._get_scores_ratios(X, Y)

        y_min = np.min(ratios)
        y_max = np.max(ratios)
        self.ir = IsotonicRegression(y_min=y_min, y_max=y_max)
        self.ir.fit(scores, ratios)

        return self

    def toLogLikelihoodRatio(self, scores):
        """Get log-likelihood ratio given scores

        Parameters
        ----------
        scores : numpy array
            Test scores

        Returns
        -------
        llr : numpy array
            Log-likelihood ratio array with same shape as input `scores`
        """
        x_min = np.min(self.ir.X_)
        x_max = np.max(self.ir.X_)

        oob_min = np.where(scores < x_min)
        oob_max = np.where(scores > x_max)
        ok = np.where((scores >= x_min) * (scores <= x_max))

        calibrated = np.zeros(scores.shape)
        calibrated[ok] = self.ir.transform(scores[ok])
        calibrated[oob_min] = self.ir.y_min
        calibrated[oob_max] = self.ir.y_max
        return calibrated


class LLRLinearRegression(LLR):
    """Log-likelihood ratio estimation by linear regression"""

    def __init__(self):
        super(LLRLinearRegression, self).__init__()

    def fit(self, X, Y):

        self.prior = self._get_prior(X, Y)

        scores, ratios = self._get_scores_ratios(X, Y)

        self.lr = LinearRegression(fit_intercept=True, normalize=False)
        self.lr.fit(scores, ratios)

        return self

    def toLogLikelihoodRatio(self, scores):
        """Get log-likelihood ratio given scores

        Parameters
        ----------
        scores : numpy array
            Test scores

        Returns
        -------
        llr : numpy array
            Log-likelihood ratio array with same shape as input `scores`
        """
        return self.lr.transform(scores)
