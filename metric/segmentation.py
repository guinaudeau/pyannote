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

SEG_PRECISION_NAME = 'precision'

class SegmentationPrecision(BaseErrorRate):
    def __init__(self, tolerance=0.):
        values = set([])
        super(SegmentationPrecision, self).__init__(SEG_PRECISION_NAME, \
                                                    values)
        self.__tolerance = tolerance
    
    def get_details(self, reference, hypothesis, **kwargs):
        
        detail = self.init_details()        
        return detail
    
    def get_rate(self, detail):
        
        numerator = 
        denominator = 
        if denominator == 0.:
            if numerator == 0:
                return 0.
            else:
                return 1.
        else:
            return numerator/denominator
       
    def pretty(self, detail):
        return string
    
    

SEG_RECALL_NAME = 'recall'
class SegmentationRecall(BaseErrorRate):
    def __init__(self, tolerance=0.):
        values = 
        super(SegmentationRecall, self).__init__(SEG_RECALL_NAME, \
                                                 values)
        self.__tolerance = tolerance

SEG_FMEASURE_NAME = 'f-measure'
class SegmentationFMeasure(object):
    def __init__(self, tolerance=0.):
        values = 
        super(SegmentationRecall, self).__init__(SEG_RECALL_NAME, \
                                                 values)
        self.__tolerance = tolerance
        

