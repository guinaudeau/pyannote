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

import itertools
import numpy as np
from pyannote.base.annotation import Unknown
from pyannote.stats.llr import LLRLinearRegression, LLRIsotonicRegression
from pyannote.stats.llr import logsumexp


class AuthenticationCalibration(object):
    """

    Parameters
    ----------
    method : {'linear', 'isotonic'}, optional
        Default is linear regression of log-likelihood ratio
    equal_priors : boolean, optional
        Defaults to False
    open_set : boolean, optional
        Defaults to False
    """

    @classmethod
    def from_file(cls, path):
        import pickle
        with open(path, mode='r') as f:
            calibration = pickle.load(f)
        return calibration

    def to_file(self, path):
        import pickle
        with open(path, mode='w') as f:
            pickle.dump(self, f)

    def __init__(
        self,
        method='linear',
        equal_priors=False, open_set=False
    ):
        super(AuthenticationCalibration, self).__init__()

        self.method = method

        if method == 'linear':
            self.llr = LLRLinearRegression()

        elif method == 'isotonic':
            self.llr = LLRIsotonicRegression()

        else:
            raise NotImplementedError(
                'unknown calibration method (%s)' % method)

        self.llr.equal_priors = True

        self.equal_priors = equal_priors
        self.open_set = open_set

    def _fit_priors(self, annotations):
        # assumes self.targets is already set

        # chart[target] = accumulated duration of target
        chart = {}

        # total = total duration of all targets
        total = 0.

        for a in annotations:

            # accumulate
            for target, duration in a.chart():

                # group all Unknowns into one unique Unknown target
                if isinstance(target, Unknown) or target not in self.targets:
                    target = Unknown

                # increment target duration
                chart[target] = chart.get(target, 0) + duration

                # increment total duration
                total = total + duration

        # normalize duration into probabilities
        self.priors = {
            target: duration/total
            for target, duration in chart.iteritems()
        }

        return self

    def _fit_llr(self, annotations, scores):

        X = []
        Y = []

        self.targets = None

        for a, s in itertools.izip(annotations, scores):

            # assumes that all scores s share the same set of labels
            if self.targets is None:
                self.targets = s.labels()

            for segment, track, label in a.itertracks(label=True):

                for target in self.targets:

                    x = s[segment, track, target]

                    if isinstance(label, Unknown):
                        y = np.nan
                    else:
                        y = np.float(label == target)

                    X.append(x)
                    Y.append(y)

        self._X = np.array(X)
        self._Y = np.array(Y)

        self.llr.fit(self._X, self._Y)

        return self

    def fit(self, scores, annotations):

        # tee annotations iterator
        # one iterator is for estimation of priors
        # the other one is for log-likelihood ratio estimation
        annotations_1, annotations_2 = itertools.tee(annotations)

        # estimate log-likelihood ratio
        # and set self.targets
        self._fit_llr(annotations_2, scores)

        # estimate target priors
        # assumes self.targets is already set
        self._fit_priors(annotations_1)

        return self

    def _llr2posterior(self, llr, priors, unknown_prior):
        """Convert log-likelihood ratios to posterior probabilities

        Parameters
        ----------
        llr :

        """
        denominator = (
            unknown_prior +
            np.exp(logsumexp(llr, b=priors, axis=1))
        )

        posteriors = ((priors * np.exp(llr)).T / denominator).T

        return posteriors

    def apply(self, scores):
        """
        Parameters
        ----------
        scores : `Scores`
        """

        # targets must be the same and ordered the same way
        assert scores.labels() == self.targets

        # get log-likelihood ratio from raw scores
        llr = scores.apply(self.llr.toLogLikelihoodRatio)

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
            priors = np.array(
                [self.priors[target]
                for target in self.targets]
            )

            # in case of close-set classification
            # equally distribute unknown prior to known targets
            if self.open_set is False:
                priors = priors + self.priors.get(Unknown, 0.)/n_targets

        # compute posterior from LLR directly on the internal numpy array
        func = lambda x: self._llr2posterior(x, priors, unknown_prior)
        return llr.apply(func)
