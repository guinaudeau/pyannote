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

# --------------------------------------------------------------------------- #

from base import Precision, Recall
from base import PRECISION_RETRIEVED, PRECISION_RELEVANT_RETRIEVED
from base import RECALL_RELEVANT, RECALL_RELEVANT_RETRIEVED
from ..base.segment import SEGMENT_PRECISION

class SegmentationPrecision(Precision):
    def __init__(self, tolerance=0.):
        super(SegmentationPrecision, self).__init__()
        self.__tolerance = max(tolerance, 1.1 * SEGMENT_PRECISION)
        
    def __get_tolerance(self): 
        return self.__tolerance
    tolerance = property(fget=__get_tolerance, \
                     fset=None, \
                     fdel=None, \
                     doc="Tolerance, in seconds.")
    
    def __segment_to_collar(self, segment):
        collar = segment.copy()
        collar.start = segment.start - .5 * self.tolerance
        collar.end =   segment.start + .5 * self.tolerance 
        return collar
        
    def get_details(self, reference, hypothesis, **kwargs):
        
        if not reference.is_partition():
            raise ValueError('Provided reference is not a partition.')
        if not hypothesis.is_partition():
            raise ValueError('Provided hypothesis is not a partition.')
        if reference.extent() != hypothesis.extent():
            raise ValueError('Reference and hypothesis extents do not match.')
                
        detail = self.init_details()        
        
        detail[PRECISION_RETRIEVED] = len(hypothesis) - 1
        R = reference.copy(map_func=self.__segment_to_collar)
        del R[0]
        H = hypothesis.copy(map_func=self.__segment_to_collar)
        del H[0]
        
        for collar in H:
            if R(collar, mode='loose'):
                detail[PRECISION_RELEVANT_RETRIEVED] += 1
        
        return detail

class SegmentationRecall(Recall):
    def __init__(self, tolerance=0.):
        super(SegmentationRecall, self).__init__()
        self.__tolerance = max(tolerance, 1.1 * SEGMENT_PRECISION)
        
    def __get_tolerance(self): 
        return self.__tolerance
    tolerance = property(fget=__get_tolerance, \
                     fset=None, \
                     fdel=None, \
                     doc="Tolerance, in seconds.")
    
    def __segment_to_collar(self, segment):
        collar = segment.copy()
        collar.start = segment.start - .5 * self.tolerance
        collar.end =   segment.start + .5 * self.tolerance 
        return collar
        
    def get_details(self, reference, hypothesis, **kwargs):
        
        if not reference.is_partition():
            raise ValueError('Provided reference is not a segmentation.')
        if not hypothesis.is_partition():
            raise ValueError('Provided hypothesis is not a segmentation.')
        if reference.extent() != hypothesis.extent():
            raise ValueError('Reference and hypothesis extents do not match.')
                
        detail = self.init_details()        
        
        detail[RECALL_RELEVANT] = len(reference) - 1
        R = reference.copy(map_func=self.__segment_to_collar)
        del R[0]
        H = hypothesis.copy(map_func=self.__segment_to_collar)
        del H[0]
        
        for collar in R:
            if H(collar, mode='loose'):
                detail[RECALL_RELEVANT_RETRIEVED] += 1
        
        return detail
        
if __name__ == "__main__":
    import doctest
    doctest.testmod()

