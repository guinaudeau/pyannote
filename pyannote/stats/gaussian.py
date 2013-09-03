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


class Gaussian(object):

    def __init__(self, covariance_type='full'):

        if covariance_type not in ['full', 'diag']:
            raise ValueError("Invalid value for covariance_type: %s"
                             % covariance_type)

        super(Gaussian, self).__init__()
        self.covariance_type = covariance_type

    def __set_covar(self, covar):
        """Set covariance and reset its inverse & log-determinant"""
        self._covar = covar
        self._inv_covar = None
        self._log_det_covar = None

    def __get_covar(self):
        """Get covariance"""
        return self._covar

    covar = property(fset=__set_covar, fget=__get_covar)
    """Covariance matrix"""

    def __get_inv_covar(self):
        """Pre-compute and/or return pre-computed inverse of covariance"""

        # if it is computed already, returns it
        if self._inv_covar is not None:
            return self._inv_covar

        # otherwise, we need to compute and store it before returning it
        self._inv_covar = np.linalg.inv(self.covar)
        return self._inv_covar

    inv_covar = property(fget=__get_inv_covar)
    """Inverse of covariance matrix"""

    def __get_log_det_covar(self):
        """Pre-compute and/or return pre-computed log |covar|"""

        # if it is computed already, returns it
        if self._log_det_covar is not None:
            return self._log_det_covar

        # otherwise, we need to compute and store it before returning it
        _, self._log_det_covar = np.linalg.slogdet(self.covar)

        return self._log_det_covar

    log_det_covar = property(fget=__get_log_det_covar)
    """Logarithm of covariance determinant"""

    def fit(self, X):

        # compute gaussian mean
        self.mean = np.mean(X, axis=0).reshape((1, -1))

        # compute gaussian covariance matrix
        if self.covariance_type == 'full':
            self.covar = np.cov(X.T, ddof=0)
        elif self.covariance_type == 'diag':
            self.covar = np.diag(np.diag(np.cov(X.T, ddof=0), k=0))

        # keep track of number of samples
        self.n_samples = len(X)

        return self

    def merge(self, other):

        # number of samples
        n1 = self.n_samples
        n2 = other.n_samples
        n = n1 + n2

        # mean
        m1 = self.mean.reshape((1, -1))
        m2 = other.mean.reshape((1, -1))
        m = (n1*m1+n2*m2)/n

        # covariance
        k1 = self.covar
        k2 = other.covar
        k = 1./n * (n1*(k1+np.dot(m1.T, m1)) +
                    n2*(k2+np.dot(m2.T, m2))) \
            - np.dot(m.T, m)

        # make it diagonal if needed
        if self.covariance_type == 'diag':
            k = np.diag(np.diag(k, k=0))

        # global gaussian
        g = Gaussian(covariance_type=self.covariance_type)
        g.mean = m
        g.covar = k
        g.n_samples = n

        return g

    def bic(self, other, penalty_coef=3.5):

        # merge self and other
        g = self.merge(other)

        # number of free parameters
        d, _ = g.covar.shape
        if g.covariance_type == 'full':
            N = int(d*(d+1)/2. + d)
        elif g.covariance_type == 'diag':
            N = 2*d

        # compute delta BIC
        n = g.n_samples
        n1 = self.n_samples
        n2 = other.n_samples
        ldc = g.log_det_covar
        ldc1 = self.log_det_covar
        ldc2 = other.log_det_covar
        delta_bic = n*ldc - n1*ldc1 - n2*ldc2 - penalty_coef*N*np.log(n)

        # return delta bic & merged gaussian
        return delta_bic, g
