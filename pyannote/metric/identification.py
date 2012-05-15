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

class IDMatcher(object):
    """
    ID matcher base class.
    
    All ID matcher classes must inherit from this class and implement
    .__call__() -- ie return True if two IDs match and False 
    otherwise.
    """
    
    def __init__(self):
        super(IDMatcher, self).__init__()
    
    def __call__(self, id1, id2):
        raise NotImplementedError( \
            'IDMatcher sub-classes must implement .__call__() method.')

    def ncorrect(self, ids1, ids2):
        
        # duplicate because we are going to modify it.
        ids2 = set(ids2)
        # will contain number of matches
        count = 0
        
        # look for a match for each ID in ids1
        for id1 in ids1:
            # get list of matching IDs in ids2
            matched = set([id2 for id2 in ids2 if self(id1, id2)])
            # if we found at least one match
            if matched:
                # increment number of matches
                count += 1
                # remove one match for ids2
                ids2.remove(matched.pop())
                
        return count


# --------------------------------------------------------------------------- #

class DefaultIDMatcher(IDMatcher):
    """
    Default ID matcher: two IDs match if they are equal.
    """
    
    def __init__(self):
        super(DefaultIDMatcher, self).__init__()
    
    def __call__(self, id1, id2):
        # Two IDs match if they are equal to each other
        return id1 == id2

    def ncorrect(self, ids1, ids2):
        # Slightly faster than inherited .ncorrect() method
        return len(ids1 & ids2)
        

# --------------------------------------------------------------------------- #

from base import BaseErrorRate

IER_TOTAL = 'total'
IER_CORRECT = 'correct'
IER_CONFUSION = 'confusion'
IER_FALSE_ALARM = 'false alarm'
IER_MISS = 'miss'
IER_NAME = 'identification error rate'

from pyannote.algorithm.tagging import DirectTagger

class IdentificationErrorRate(BaseErrorRate):

    def __init__(self, matcher=None):

        values = set([ \
            IER_CONFUSION, \
            IER_FALSE_ALARM, \
            IER_MISS, \
            IER_TOTAL, \
            IER_CORRECT])

        super(IdentificationErrorRate, self).__init__(IER_NAME, values)
        
        if matcher:
            self.matcher = matcher
        else:
            self.matcher = DefaultIDMatcher()
        self.tagger = DirectTagger()
    
    def get_details(self, reference, hypothesis, **kwargs):
        
        detail = self.init_details()
        
        # common (up-sampled) timeline
        common_timeline = reference.timeline + hypothesis.timeline
        common_timeline = common_timeline.segmentation()
    
        # align reference on common timeline
        R = self.tagger(reference, common_timeline)
    
        # translate and align hypothesis on common timeline
        H = self.tagger(hypothesis, common_timeline)
    
        # loop on all segments
        for segment in common_timeline:
        
            # segment duration
            duration = segment.duration
        
            # set of IDs in reference segment
            r = R.get_labels(segment)
            Nr = len(r)
            detail[IER_TOTAL] += duration * Nr
        
            # set of IDs in hypothesis segment
            h = H.get_labels(segment)
            Nh = len(h)
        
            # number of correct matches
            # N_correct = len(r & h)
            N_correct = self.matcher.ncorrect(r, h)
            detail[IER_CORRECT] += duration * N_correct
            
            # number of incorrect matches
            N_error   = min(Nr, Nh) - N_correct
            detail[IER_CONFUSION] += duration * N_error
            
            # number of misses
            N_miss = max(0, Nr - Nh)
            detail[IER_MISS] += duration * N_miss
            
            # number of false alarms
            N_fa = max(0, Nh - Nr)
            detail[IER_FALSE_ALARM] += duration * N_fa
        
        return detail
    
    def get_rate(self, detail):
        
        numerator = 1. * (detail[IER_CONFUSION] + \
                          detail[IER_FALSE_ALARM] + \
                          detail[IER_MISS])
        denominator = 1. * detail[IER_TOTAL]
        if denominator == 0.:
            if numerator == 0:
                return 0.
            else:
                return 1.
        else:
            return numerator/denominator
       
    def pretty(self, detail):
        string = ""
        string += "  - duration: %.2f seconds\n" % (detail[IER_TOTAL])
        string += "  - correct: %.2f seconds\n" % (detail[IER_CORRECT])
        string += "  - confusion: %.2f seconds\n" % (detail[IER_CONFUSION])
        string += "  - miss: %.2f seconds\n" % (detail[IER_MISS])
        string += "  - false alarm: %.2f seconds\n" % (detail[IER_FALSE_ALARM])
        string += "  - %s: %.2f %%\n" % (self.name, 100*detail[self.name])
        return string

if __name__ == "__main__":
    import doctest
    doctest.testmod()
