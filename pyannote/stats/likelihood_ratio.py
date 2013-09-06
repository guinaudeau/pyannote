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

import sc2llr
import numpy as np


class LogLikelihoodRatioLinearRegression(object):
    """Log-likelihood ratio estimation by linear regression"""

    def __init__(self):
        super(LogLikelihoodRatioLinearRegression, self).__init__()

    def fit(self, positive, negative, prior=None):
        """Train linear regression on log-likelihood ratio

        Parameters
        ----------
        positive, negative : numpy array
            Positve (a.k.a target or client) and negative (a.k.a non-target or
            impostor) scores

        prior : float, optional
            By default, prior is estimated based on the number of positive
            and negative scores.

        """

        # Prior estimation
        if prior is None:
            self.prior = 1. * len(positive) / (len(positive) + len(negative))
        else:
            self.prior = prior

        # Log-likelihood ratio estimation
        self.a, self.b = sc2llr.computeLinearMapping(negative, positive, nb=15)

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
        return self.a * scores + self.b

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
        logLikelihoodRatio = self.toLogLikelihoodRatio(scores)

        # Get prior
        if prior is None:
            prior = self.prior
        priorRatio = (1.-prior) / prior

        # Compute posterior probability
        return 1/(1+priorRatio*np.exp(-logLikelihoodRatio))
