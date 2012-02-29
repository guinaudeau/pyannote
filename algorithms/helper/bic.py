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

import sklearn.mixture

class Gaussian(sklearn.mixture.GMM):
    """
    Gaussian for BIC segmentation & clustering
    
    g = g1 + g2 : merge gaussian
    d = g1 | g2 : delta BIC
    """
    def __init__(self, penalty=7.0):
        
        super(Gaussian, self).__init__(n_components=1, \
                                       cvtype='full', \
                                       random_state=None)

        # Number of samples
        self.__n_samples = -1

        # Pre-computed n * log |covar|
        self.__nlogdet = None

        # Lambda for penalty on model size
        self.__penalty = penalty
    
    def __get_n_samples(self): 
        return self.__n_samples
    def __set_n_samples(self, n_samples): 
        self.__n_samples = n_samples
    n_samples = property(fget=__get_n_samples, \
                         fset=__set_n_samples, \
                         fdel=None, \
                         doc="Number of samples.")
    
    def __get_penalty(self): 
        return self.__penalty
    penalty = property(fget=__get_penalty, \
                         fset=None, \
                         fdel=None, \
                         doc="Number of samples.")
                         
    def __get_dimension(self): 
        return self.n_features
    dimension = property(fget=__get_dimension, \
                         fset=None, \
                         fdel=None, \
                         doc="Feature space dimension.")
    

    def __update_nlogdet(self):
        # make sure cov is a square matrix
        D = self.dimension
        cov = self.covars.reshape(D, D)
        # actual computation of N x log( det(sigma) )
        N = self.n_samples
        self.__nlogdet = N*np.log(np.linalg.det(cov))

    def __get_nlogdet(self): 
        if self.__nlogdet is None:
            self.__update_nlogdet()
        return self.__nlogdet
    nlogdet = property(fget=__get_nlogdet, \
                         fset=None, \
                         fdel=None, \
                         doc="N x log( det(sigma) )")

    def fit(self, X):
        # inherits .fit()
        # ... updates .means and .covars
        super(Gaussian, self).fit(X, n_iter=0, init_params='wmc')
        # keeps track of number of samples
        N, D = X.shape
        self.n_samples = N
        return self
    
    def __and__(self, other):
        """
        Merge two Gaussians into one
        """
        # do dimensions match?
        D = self.dimension
        if D != other.dimension:
            raise ValueError('Dimension mismatch')
        
        # do penalty coefficients match?
        penalty = self.penalty
        if penalty != other.penalty:
            raise ValueError('Penalty coefficient mismatch')
        
        # new 'empty' Gaussian
        cls = type(self)
        G = cls(penalty=penalty)
        
        # set number of samples for new Gaussian
        n1 = self.n_samples
        n2 = other.n_samples
        n = n1 + n2        
        G.n_samples = n
        
        # set dimension of new Gaussian
        G.n_features = D
        
        # set mean of new Gaussian
        mu1 = self.means
        mu2 = other.means        
        mu = (n1 * mu1 + n2 * mu2) / (n1 + n2)
        G.means = mu
        
        # set covariance of new Gaussian
        c1 = self.covars
        c2 = other.covars
        c = (n1*c1 + \
             n2*c2 + \
             n1*np.dot(mu1.T, mu1) + \
             n2*np.dot(mu2.T, mu2)) / (n1+n2) - np.dot(mu.T, mu)
        G.covars = c
                
        return G
            
    def __sub__(self, other):
        """
        Compute \Delta BIC
        g1 - g2 == g2 - g1 == \Delta BIC(g1, g2)
        """
        
        # do dimensions match?
        D = self.dimension
        if D != other.dimension:
            raise ValueError('Dimension mismatch')
        
        # do penalty coefficients match?
        penalty = self.penalty
        if penalty != other.penalty:
            raise ValueError('Penalty coefficient mismatch')
                
        # merge two Gaussians
        G = self & other
        
        # model size penalty
        N = G.n_samples
        P = .5*(D+0.5*D*(D+1))*np.log(N)
        
        # final \Delta BIC
        return G.nlogdet - self.nlogdet - other.nlogdet - penalty*P
