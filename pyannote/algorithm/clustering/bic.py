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


from pyannote.algorithm.clustering.base import BaseAgglomerativeClustering
from pyannote.base.matrix import LabelMatrix
from pyannote.algorithm.util.bic import BIC_Gaussian

class BICClustering(BaseAgglomerativeClustering):
    
    def __init__(self, penalty=3.5):
        super(BICClustering, self).__init__()
        self.__penalty = penalty
    
    def _compute_model(self, label):
        # extract features for this label
        data = self.feature(self.annotation(label).timeline)
        # fit mono-gaussian and return it
        return BIC_Gaussian(penalty=self.__penalty).fit(data)
    
    def _initialize(self):
        self.__M = LabelMatrix()
        labels = self.annotation.labels()
        for l, label in enumerate(labels):
            model = self.models[label]
            for other_label in labels[l+1:]:
                other_model = self.models[other_label]
                distance = model - other_model
                self.__M[label, other_label] = distance
                self.__M[other_label, label] = distance
    
    def _next(self):
        label1, label2 = self.__M.argmin().popitem()
        distance = self.__M[label1, label2]
        if distance < 0:
            return sorted([label1, label2])
        else:
            return []
    
    def _merge_models(self, labels):
        new_model = self.models[labels[0]]
        for label in labels[1:]:
            new_model = new_model & self.models[label]
        return new_model
    
    def _update(self, new_label, old_labels):
        
        # remove rows and columns for old labels
        for old_label in old_labels:
            del self.__M[old_label, :]
            del self.__M[:, old_label]
        
        # update row and column for new label
        labels = self.annotation.labels()
        model = self.models[new_label]
        for other_label in labels:
            if other_label != new_label:
                other_model = self.models[other_label]
                distance = model - other_model
                self.__M[new_label, other_label] = distance
                self.__M[other_label, new_label] = distance


if __name__ == "__main__":
    import doctest
    doctest.testmod()
  