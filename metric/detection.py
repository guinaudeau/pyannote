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

from base import BaseErrorRate

DER_TOTAL = 'total'
DER_FALSE_ALARM = 'false alarm'
DER_MISS = 'miss'
DER_NAME = 'detection error rate'

class DetectionErrorRate(BaseErrorRate):

    def __init__(self):

        numerator = {DER_FALSE_ALARM: 1., DER_MISS: 1., }
        denominator = {DER_TOTAL: 1., }
        other = []
        
        super(DetectionErrorRate, self).__init__(DER_NAME, numerator, denominator, other)
    
    
    def __call__(self, reference, hypothesis, detailed=False):
        
        detail = self.initialize()
        
        # common (up-sampled) timeline
        common_timeline = abs(reference.timeline + hypothesis.timeline)
    
        # align reference on common timeline
        R = reference >> common_timeline
    
        # translate and align hypothesis on common timeline
        H = hypothesis >> common_timeline
    
        # loop on all segments
        for segment in common_timeline:
        
            # segment duration
            duration = abs(segment)
        
            # set of IDs in reference segment
            r = R.ids(segment)
            Nr = len(r)
            detail[DER_TOTAL] += duration * Nr
        
            # set of IDs in hypothesis segment
            h = H.ids(segment)
            Nh = len(h)
        
            # number of misses
            N_miss = max(0, Nr - Nh)
            detail[DER_MISS] += duration * N_miss
        
            # number of false alarms
            N_fa = max(0, Nh - Nr)
            detail[DER_FALSE_ALARM] += duration * N_fa
    
        return self.compute(detail, accumulate=True, detailed=detailed)
        
    def pretty(self, detail):
        
        string = ""
        
        string += "  - duration: %g" % (detail[DER_TOTAL])
        string += "\n"
    
        string += "  - miss: %g" % (detail[DER_MISS])
        string += "\n"
        
        string += "  - false alarm: %g" % (detail[DER_FALSE_ALARM])
        string += "\n"
    
        string += "  - %s: %g %%" % (self.name, 100*detail[self.name])
        string += "\n"
        
        return string
