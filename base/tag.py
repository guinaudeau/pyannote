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

from segment import Segment
from timeline import Timeline
from collections import Hashable

UNIQUE_TRACK = '__@__'
UNIQUE_LABEL = '__@__'

class BaseTag(object):
    
    def __init__(self, multitrack=True, modality=None, video=None):
        
        super(BaseTag, self).__init__()
        self.__multitrack = multitrack
        self.__modality = modality
        self.__video = video
        self.timeline = Timeline(video=self.video)
        self.data = {}
        self.tag_timeline = {}
        self.tag_count = {}

    def __get_multitrack(self):
        return self.__multitrack
    multitrack = property(fget=__get_multitrack, fset=None, fdel=None, \
                          doc="Can segments contain multiple tracks?")
    
    def __get_video(self): 
        return self.__video
    video = property(fget=__get_video, fset=None, fdel=None, \
                     doc="Annotated video.")

    def __get_modality(self): 
        return self.__modality
    modality = property(fget=__get_modality, fset=None, fdel=None, \
                        doc="Annotated modality.")    
    
    def __get_IDs(self):
        return self.tag_count.keys()
    IDs = property(fget=__get_IDs, fset=None, fdel=None, \
                   doc="List of labels.")
    
    def valid_segment(self, segment):
        return isinstance(segment, Segment) and segment
    
    def valid_track(self, track):
        return isinstance(track, Hashable)
    
    def valid_label(self, label):
        return isinstance(label, Hashable)
    

class Unknown(object):
    nextID = 0
    """
    Keep track of the number of instances since last reset
    """
    
    @classmethod
    def reset(cls):
        cls.nextID = 0
    
    @classmethod
    def next(cls):
        cls.nextID += 1
        return cls.nextID
    
    def __init__(self, format='Unknown%03d'):
        super(Unknown, self).__init__()
        self.ID = Unknown.next()
        self.format = format
    
    def __str__(self):
        return self.format % self.ID
    
    def __repr__(self):
        return '?'
        
    def __hash__(self):
        return hash(self.ID)
        
    def __eq__(self, other):
        if isinstance(other, Unknown):
            return self.ID == other.ID
        else:
            return False

class MonoTag(BaseTag):
    
    def __init__(self, multitrack=True, video=None, modality=None):        
        super(MonoTag, self).__init__(multitrack=multitrack, \
                                      video=video, \
                                      modality=modality)
    
    def ids(self, segment):
        if segment not in self:
            return set([])
        return set([self.data[segment][track] \
                    for track in self.data[segment]])
    
    def parse_key(self, key):
        if self.multitrack:
            if (not isinstance(key, tuple)) or (len(key) != 1+self.multitrack):
               raise KeyError('')
            segment = key[0]
            track = key[1]            
        else:
            if (not isinstance(key, Segment)):
                raise KeyError('')
            segment = key
            track = UNIQUE_TRACK
        return segment, track
    
    def __getitem__(self, key):
        
        segment, track = self.parse_key(key)
        
        if track == slice(None,None,None):
            return dict(self.data[segment])
        else:
            return self.data[segment][track]
    
    def __setitem__(self, key, label):
        
        segment, track = self.parse_key(key)
        
        if not self.valid_segment(segment):
            raise KeyError('')
        if not self.valid_track(track):
            raise KeyError('')
        if not self.valid_label(label):
            raise ValueError('')

        # do nothing or delete existing label
        if (segment in self.data) and (track in self.data[segment]):
            if self.data[segment][track] == label:
                return
            else:
                self.__delitem__(key)

        # update .timeline
        if segment not in self.timeline:
            self.timeline += segment
            self.data[segment] = {}

        # update .data
        self.data[segment][track] = label
        
        # update .tag_timeline
        if label not in self.tag_timeline:
            self.tag_timeline[label] = Timeline(video=self.video)
        self.tag_timeline[label] += segment

        # update .tag_count
        if label not in self.tag_count:
            self.tag_count[label] = {}
        if segment not in self.tag_count[label]:
            self.tag_count[label][segment] = 0
        self.tag_count[label][segment] += 1
    
    def __delitem__(self, key):
        
        segment, track = self.parse_key(key)
        
        # del T[segment, :]
        if track == slice(None,None,None):
            for t in self.data[segment].keys():
                print "del T[segment, %s]" % t
                self.__delitem__((segment, t))
            return
        
        # del T[segment, track]
        label = self.data[segment][track]
        
        # update .data & .timeline
        del self.data[segment][track]
        if not self.data[segment]:
            del self.data[segment]
            del self.timeline[segment]
        
        # update .tag_count & .tag_timeline
        self.tag_count[label][segment] -= 1
        if self.tag_count[label][segment] == 0:
            del self.tag_count[label][segment]
            if not self.tag_count[label]:
                del self.tag_count[label]
            del self.tag_timeline[label][segment]
            if not self.tag_timeline[label]:
                del self.tag_timeline[label]
    
    def __len__(self):
        return len(self.timeline)
    
    def __nonzero__(self):
        return len(self.timeline) > 0
        
    def __contains__(self, segment):
        return segment in self.timeline
    
    def __iter__(self):
        return iter(self.timeline)

    def __reversed__(self):
        return reversed(self.timeline)
    
    def iterlabels(self):
        for segment in self:
            for track in self.data[segment]:
                if self.multitrack:
                    yield segment, track, self.data[segment][track]
                else:
                    yield segment, self.data[segment][track]
    
    def empty(self):
        """
        Return empty copy.
        """
        T = type(self)(multitrack=self.multitrack, \
                       video=self.video, \
                       modality=self.modality)
        return T
    
    def copy(self, segment_func=None, track_func=None, label_func=None):
        """
        Return copy.
        - segment_in_copy = segment_func(original_segment)
        - track_in_copy = track_func(original_track)
        - label_in_copy = label_func(original_label)
        """
        T = self.empty()
        
        if segment_func is None:
            segment_func = lambda s: s
        if track_func is None:
            track_func = lambda t: t
        if label_func is None:
            label_func = lambda l: l
        
        if self.multitrack:
            for segment, track, label in self.iterlabels():
                new_segment = segment_func(segment)
                if new_segment:
                    T[new_segment, track_func(track)] = label_func(label)
        else:
            for segment, label in self.iterlabels():
                if segment_func(segment):
                    T[segment_func(segment)] = label_func(label)
        
        return T
                
    def __mod__(self, translation):
        """
        More or less equivalent to copy(label_func=translation)
        """

        if not isinstance(translation, (dict, OneToOneMapping)):
            raise TypeError('Translation must be dict or OneToOneMapping.')
        
        label_func = lambda x: translation[x] if translation[x] else x
        return self.copy(label_func=label_func)    
    
    def __get_label(self, label):
        
        T = self.empty()
        
        if self.multitrack:
            for segment in self.tag_timeline[label]:
                for track in self.data[segment]:
                    if self.data[segment][track] == label:
                        T[segment, track] = label
        else:
            for segment in self.tag_timeline[label]:
                for track in self.data[segment]:
                    if self.data[segment][track] == label:
                        T[segment] = label
        
        return T    
            
    def __call__(self, subset, mode='strict', invert=False):
        """
        """
        # get temporal slices
        if isinstance(subset, Segment):
            segment = subset
            timeline = Timeline(video=self.video)
            timeline += segment
            return self.__call__(timeline, mode=mode, invert=invert)            
        
        elif isinstance(subset, Timeline):
            
            timeline = subset
            
            if invert:
                timeline = self.timeline.coverage() / timeline
                return self.__call__(timeline, mode=mode, invert=False)
            
            coverage = timeline.coverage()
            if mode == 'strict':
                segment_func = lambda s : s if coverage.covers(s) else False 
            else:
                raise ValueError('unsupported mode.')
                
            return self.copy(segment_func=segment_func)

        
        # get set of labels
        elif isinstance(subset, (tuple, list, set)):
            
            # if invert, get the complementary set of labels
            # otherwise, make sure it is a set (not list or tuple)
            if invert:
                labels = set(self.IDs) - set(subset)
            else:
                labels = set(subset)
            
            T = self.empty()

            for label in labels:
                t = self.__get_label(label)
                if self.multitrack:
                    for segment, track, label in t.iterlabels():
                        T[segment, track] = label
                else:
                    for segment, label in t.iterlabels():
                        T[segment] = label
            
            return T
        
        # get one single label
        else:
            # one single label == set of one label
            return self.__call__(set([subset]), mode=mode, invert=invert)
    
    def show(self):
        if self.multitrack:
            for segment, track, label in self.iterlabels():
                print segment, track, label
        else:
            for segment, label in self.iterlabels():
                print segment, label
    
            
