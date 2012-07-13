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

from pyannote.algorithm.clustering.model.base import BaseModelMixin
from Levenshtein import jaro
import numpy as np


class SameStringMMx(BaseModelMixin):
    def mmx_symmetric(self):
        return True
    
    def mmx_fit(self, label):
        return tuple([label])
    
    def mmx_merge(self, labels):
        new_model = []
        for label in labels:
            other_model = self.models[label]
            new_model.extend(other_model)
        return tuple(new_model)
    
    def mmx_compare(self, label, other_label):
        model = self.models[label]
        other_model = self.models[other_label]
        return np.mean([float(s == t) for s in model for t in other_model])

class LevenshteinMMx(BaseModelMixin):
    
    def mmx_symmetric(self):
        return True
    
    def mmx_fit(self, label):
        return tuple([label])
    
    def mmx_merge(self, labels):
        new_model = []
        for label in labels:
            other_model = self.models[label]
            new_model.extend(other_model)
        return tuple(new_model)
    
    def mmx_compare(self, label, other_label):
        model = self.models[label]
        other_model = self.models[other_label]
        return np.mean([jaro(s, t) for s in model for t in other_model])


if __name__ == "__main__":
    import doctest
    doctest.testmod()

