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


from pyannote.algorithm.clustering.mmx.base import BaseModelMixin
from pyannote.algorithm.util.gaussian import Gaussian

class GaussianMMx(BaseModelMixin):
    """Mono-gaussian model mixin
    
    Parameter
    ---------
    covariance_type : {'diag', 'full'}, optional
        Default is 'full' covariance matrix.
    """
    
    
    def mmx_setup(self, covariance_type='full', **kwargs):
        """Model mixin setup
        
        Parameters
        ----------
        covariance_type : {'diag', 'full'}, optional
            Default is 'full' covariance matrix.
        """
        self.mmx_covariance_type = covariance_type
    
    def mmx_fit(self, label):
        """Fit one gaussian to label features
        
        Parameters
        ----------
        label : hashable object
            A label existing in processed `annotation`
        
        Returns
        -------
        g : :class:`pyannote.algorithm.util.gaussian.Gaussian`
            A Gaussian fitted to label features
        
        """
        # extract features for this label
        data = self.feature(self.annotation.label_timeline(label))
        # fit gaussian and return it
        return Gaussian(covariance_type=self.mmx_covariance_type).fit(data)
    
    def mmx_merge(self, labels):
        """Merge Gaussians
        
        Merge multiple labels into one.
        
        """
        new_model = self.models[labels[0]]
        for label in labels[1:]:
            new_model = new_model.merge(self.models[label])
        return new_model


class BICMMx(GaussianMMx):
    """Bayesian Information Criterion model mixin
    
    Parameters
    ----------
    covariance_type : {'diag', 'full'}, optional
        Default is 'full' covariance matrix.
    penalty_coef : float, optional
        Coefficient for size model penalty. Default is 3.5
    
    """
    
    def mmx_setup(self, covariance_type='full', penalty_coef=3.5, **kwargs):
        """Model mixin setup
        
        Parameters
        ----------
        covariance_type : {'diag', 'full'}, optional
            Default is 'full' covariance matrix.
        penalty_coef : float, optional
            Coefficient for size model penalty. Default is 3.5
        """
        super(BICMMx, self).mmx_setup(covariance_type=covariance_type)
        self.mmx_penalty_coef = penalty_coef
    
    def mmx_symmetric(self):
        return True
    
    def mmx_compare(self, label, other_label):
        """Compute dBIC
        
        See also
        --------
        :meth:`pyannote.algorithm.util.gaussian.Gaussian.bic`
        
        """
        model = self.models[label]
        other_model = self.models[other_label]
        dissimilarity, _ = model.bic(other_model,
                                     penalty_coef=self.mmx_penalty_coef)
        return (-dissimilarity)


import numpy as np
class BICSigmoidMMx(BICMMx):
    
    def mmx_setup(self, sigmoid=1e3, **kwargs):
        super(BICSigmoidMMx, self).mmx_setup(**kwargs)
        self.mmx_sigmoid = sigmoid
    
    def mmx_compare(self, label, other_label):
        similarity = super(BICSigmoidMMx,
                           self).mmx_compare(label, other_label)
        return 1. / (1. + np.exp(-similarity/self.mmx_sigmoid))
        
    def mmx_symmetric(self):
        return False


class GaussianLikelihoodMMx(GaussianMMx):
    """"""
    
    def mmx_symmetric(self):
        return False
    
    def mmx_compare(self, label, other_label):
        other_data = self.feature(self.annotation.label_timeline(other_label))
        model = self.models[label]
        logprob = model.score(other_data)
        return np.mean(np.exp(logprob))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
