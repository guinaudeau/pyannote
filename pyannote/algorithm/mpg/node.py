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

import re

class IdentityNode(object):
    """Identity node [I]
    
    Parameters
    ----------
    identifier : any hashable object
        Unique identifier.
    """
    def __init__(self, identifier):
        super(IdentityNode, self).__init__()
        self.identifier = identifier
    
    def __eq__(self, other):
        return isinstance(other, IdentityNode) and \
               self.identifier == other.identifier
    
    def __hash__(self):
        return hash(self.identifier)
    
    def __str__(self):
        return "%s" % (self.identifier)
    
    def short(self):
        names = re.split('[ \-_]+', str(self.identifier))
        return "".join([name[0] for name in names[:-1]]) + "." + names[-1]
        
    def __repr__(self):
        return "<IdentityNode %s>" % self.identifier



class LabelNode(object):
    """Label node [L]
    
    Parameters
    ----------
    uri : any hashable object
        Unique resource identifier
    modality : any hashable object
        Unique modality identifier
    label : any hashable object
        Unique label identifier
    """
    def __init__(self, uri, modality, label):
        super(LabelNode, self).__init__()
        self.uri = uri
        self.modality = modality
        self.label = label
    
    def __eq__(self, other):
        return isinstance(other, LabelNode) and \
               self.uri == other.uri and \
               self.modality == other.modality and \
               self.label == other.label
    
    def __hash__(self):
        return hash(self.uri) + hash(self.label)
    
    def __str__(self):
        return "%s|%s" % (self.modality, self.label)
    
    def __repr__(self):
        return "<LabelNode %s>" % self


class TrackNode(object):
    """Track node [T]
    
    Parameters
    ----------
    uri : any hashable object
        Unique resource identifier
    modality : any hashable object
        Unique modality identifier
    segment : Segment
        Segment
    track : any hashable object
        Track identifier
    
    """
    def __init__(self, uri, modality, segment, track):
        super(TrackNode, self).__init__()
        self.uri = uri
        self.modality = modality
        self.segment = segment
        self.track = track
    
    def __eq__(self, other):
        return isinstance(other, TrackNode) and \
               self.uri == other.uri and \
               self.modality == other.modality and \
               abs(self.segment.start - other.segment.start) < 0.01 and \
               abs(self.segment.end - other.segment.end) < 0.01 and \
               self.track == other.track
    
    def __hash__(self):
        return hash(self.uri) + hash(self.track)
    
    def __str__(self):
        return "%s|%s_%s" % (self.modality, self.segment, self.track)
    
    def __repr__(self):
        return "<TrackNode %s>" % self
    
    def __contains__(self, other):
        """True if `other` is a sub-track"""
        assert isinstance(other, TrackNode), \
               "%r is not a track node" % other
        
        return (other.track == self.track) & \
               (other.segment in self.segment) & \
               (other.uri == self.uri) & \
               (other.modality == self.modality)
