#!/usr/bin/env python
# encoding: utf-8

# --------------------------------------------------------------------------- #

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

CONFUSION_NAME =        'Cooccurrence       '
FALSE_ALARM_NAME =      'False Alarm     '
MISSED_DETECTION_NAME = 'Missed Detection' 

class CooccurrenceError(object):
    def __init__(self, reference, hypothesis):
        super(CooccurrenceError, self).__init__()
        self.__reference = reference
        self.__hypothesis = hypothesis
        
    def __get_reference(self):
        return self.__reference
    def __get_hypothesis(self):
        return self.__hypothesis
    reference = property(fget=__get_reference, \
                     fset=None, \
                     fdel=None, \
                     doc="Reference")
    hypothesis = property(fget=__get_hypothesis, \
                     fset=None, \
                     fdel=None, \
                     doc="Hypothesis")
    
    
    
    def __hash__(self):
        return hash(self.__reference) + hash(self.__hypothesis)
    
    def __eq__(self, other):
        return self.__reference == other.__reference and \
               self.__hypothesis == other.__hypothesis
    
    def __str__(self):
        return "%s [%s | %s]" % (CONFUSION_NAME, \
                                 self.reference, \
                                 self.hypothesis)                               
    
    def __repr__(self):
        return str(self)
        
class FalseAlarmError(CooccurrenceError):
    def __init__(self, hypothesis):
        super(FalseAlarmError, self).__init__(None, hypothesis)

    def __str__(self):
        return "%s [%s]" % (FALSE_ALARM_NAME, \
                            self.hypothesis)

class MissedDetectionError(CooccurrenceError):
    def __init__(self, reference):
        super(MissedDetectionError, self).__init__(reference, None)

    def __str__(self):
        return "%s [%s]" % (MISSED_DETECTION_NAME, \
                            self.reference)

from identification import DefaultIDMatcher
from pyannote.base.mapping import OneToOneMapping, NoMatch
from pyannote.base.annotation import Annotation

class Diff(object):
    
    def __init__(self, matcher=None):
        super(Diff, self).__init__()
        if matcher:
            self.__matcher = matcher
        else:
            self.__matcher = DefaultIDMatcher()
        
    def __call__(self, reference, hypothesis):
        
        timeline = abs(reference.timeline + hypothesis.timeline) 
        
        reference = reference >> timeline
        hypothesis = hypothesis >> timeline
        
        inventory = Annotation(video=reference.video, \
                                 modality=reference.modality)
        
        for segment in timeline:
            R = reference.ids(segment)
            H = hypothesis.ids(segment)
            matching = self.__diff(R, H)
            for r, h in matching.to_dict(single=True).iteritems():
                if isinstance(r, NoMatch):
                    error = FalseAlarmError(h)
                elif isinstance(h, NoMatch):
                    error = MissedDetectionError(r)
                else:
                    error = CooccurrenceError(r, h)
                inventory[segment, error] = True
        
        return inventory

    def __diff(self, ids1, ids2):
        
        # duplicate because we are going to modify it.
        ids1_cp = set(ids1)
        ids2_cp = set(ids2)
        
        mapping = OneToOneMapping('reference', 'hypothesis')
        for id1 in ids1:
            # get list of matching IDs in ids2
            matched = set([id2 for id2 in ids2 if self.__matcher(id1, id2)])
            # if we found at least one match
            if matched:
                ids1_cp.remove(id1)
                ids2_cp.remove(matched.pop())
        
        # confusions
        for id1 in set(ids1_cp):
            if ids2_cp:
                mapping += ([id1], [ids2_cp.pop()])
                ids1_cp.remove(id1)
        
        # missed detections
        for id1 in ids1_cp:
            mapping += ([id1], None)

        # false alarms
        for id2 in ids2_cp:
            mapping += (None, [id2])
        
        return mapping
    
    def aggregate(self, inventory):
        return {identifier: inventory(identifier).timeline.duration() \
                for identifier in inventory.IDs}
        

if __name__ == "__main__":
    import doctest
    doctest.testmod()

        