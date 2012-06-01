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

"""This module defines label model mixins for agglomerative clustering.
"""

from pyannote.algorithm.clustering.base import BaseModelMixin
from pyannote.algorithm.util.gaussian import Gaussian

class BICMMx(BaseModelMixin):
    
    def mmx_setup(self, covariance_type='full', penalty_coef=3.5, **kwargs):
        self.mmx_covariance_type = covariance_type
        self.mmx_penalty_coef = penalty_coef
    
    def mmx_fit(self, label):
        """
        One Gaussian per track
        """
        # extract features for this label
        data = self.feature(self.annotation.label_timeline(label))
        # fit gaussian and return it
        return Gaussian(covariance_type=self.mmx_covariance_type).fit(data)
    
    def mmx_compare(self, label, other_label):
        """
        Delta BIC between two Gaussians
        """
        model = self.models[label]
        other_model = self.models[other_label]
        dissimilarity, _ = model.bic(other_model,
                                     penalty_coef=self.mmx_penalty_coef)
        return (-dissimilarity)
    
    def mmx_merge(self, labels):
        """
        Fast merge of two Gaussians
        """
        new_model = self.models[labels[0]]
        for label in labels[1:]:
            new_model = new_model.merge(self.models[label])
        return new_model

import numpy as np
class BICSigmoidMMx(BICMMx):
    
    def mmx_setup(self, sigmoid=1e3, **kwargs):
        super(BICSigmoidMMx, self).mmx_setup(**kwargs)
        self.mmx_sigmoid = sigmoid
    
    def mmx_compare(self, label, other_label):
        similarity = super(BICSigmoidMMx,
                           self).mmx_compare(label, other_label)
        return 1. / (1. + np.exp(-similarity/self.mmx_sigmoid))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
