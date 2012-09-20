#!/usr/bin/env python
# encoding: utf-8

# Copyright 2012 Herve BREDIN (bredin@limsi.fr)

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
from sklearn import mixture

class Gaussian(mixture.GMM):
    
    def __init__(self, covariance_type='full'):
        
        if covariance_type not in ['full', 'diag']:
            raise ValueError("Invalid value for covariance_type: %s" 
                             % covariance_type) 
        
        super(Gaussian, self).__init__(n_components=1,
                                       covariance_type=covariance_type,
                                       n_iter=0, init_params='wmc')
        # other parameters include:
        # random_state=0, 
        # thresh = Converge threshold,
        # n_init = Number of initializations,
        # params='wmc'
        
        # mean as vector
        self._mean = None
        
        # covariance matrix as a D x D matrix
        # (computed on demand)
        # NB: sklearn stores 'diag' and 'full' matrices differently...
        self._covar = None
        
        # inverse of covariance matrix
        # (computed on demand)
        self._inv_covar = None
        
        # logarithm of covariance determinant
        # (computed on demand)
        self._log_det_covar = None
        
        # number of samples used for fitting
        self._n_samples = None
    
    
    def __get_n_samples(self):
        return self._n_samples
    def __set_n_samples(self, n):
        self._n_samples = n
    def __del_n_samples(self):
        self._n_samples = None
    n_samples = property(fget=__get_n_samples, fset=__set_n_samples, 
                         fdel=__del_n_samples)
    """Number of samples used for fitting"""
    
    def __get_mean(self):
        """Pre-format and/or return pre-formated mean"""
        # if it is computed already, returns it.
        if self._mean is not None:
            return self._mean
        
        # otherwise, we need to compute and store it before returning it
        self._mean = self.means_[0]
        return self._mean
    
    def __del_mean(self):
        self._mean = None
    
    mean = property(fget=__get_mean, fdel=__del_mean)
    """Formatted mean"""
    
    def __get_covar(self):
        """Pre-format and/or return pre-formated covariance"""
        
        # if it is computed already, returns it.
        if self._covar is not None:
            return self._covar
        
        # otherwise, we need to compute and store it before returning it
        if self.covariance_type == 'full':
            self._covar = self.covars_[0]
        elif self.covariance_type == 'diag':
            self._covar = np.diag(self.covars_[0])
        return self._covar
        
    def __del_covar(self):
        self._covar = None
        self._inv_covar = None
        self._log_det_covar = None
        
    covar = property(fget=__get_covar, fdel=__del_covar)
    """Formatted covariance matrix"""
    
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
        # self._log_det_covar = np.log(np.linalg.det(self.covar))
        return self._log_det_covar
    
    log_det_covar = property(fget=__get_log_det_covar)
    """Logarithm of covariance determinant"""
    
    def fit(self, X):
        super(Gaussian, self).fit(X)
        del self.covar
        del self.mean
        self.n_samples = len(X)
        return self
    
    def merge(self, other):
        
        g = Gaussian(covariance_type=self.covariance_type)
        
        # set number of samples
        n_samples = self.n_samples
        other_n_samples = other.n_samples
        g.n_samples = n_samples + other_n_samples
        
        # compute merged means
        means = self.means_
        other_means = other.means_
        new_means = (n_samples*means+other_n_samples*other_means)/g.n_samples
        g.means_ = new_means
        
        # compute merged covariance
        covar = self.covar
        other_covar = other.covar
        new_covar = 1./g.n_samples * \
                       (n_samples*covar \
                        + other_n_samples*other_covar \
                        + n_samples*np.dot(means.T, means) \
                        + other_n_samples*np.dot(other_means.T, other_means)) \
                    - np.dot(new_means.T, new_means)
        
        d = new_covar.shape[0]
        if g.covariance_type == 'full':
            g.covars_ = np.reshape(new_covar, (1, d, d))
        elif g.covariance_type == 'diag':
            g.covars_ = np.reshape(np.diag(new_covar), (1, d))
        
        return g
    
    def bic(self, other, penalty_coef=3.5):
        
        # sklearn.mixture.GMM has a .bic method (called with data)
        if not isinstance(other, Gaussian):
            return super(Gaussian, self).bic(other)
        
        # merge self and other
        g = self.merge(other)
        
        # compute delta BIC
        delta_bic = g.n_samples * g.log_det_covar \
                    - self.n_samples * self.log_det_covar \
                    - other.n_samples * other.log_det_covar \
                    - .5*penalty_coef * g._n_parameters() * np.log(g.n_samples)
        
        return delta_bic, g
    
