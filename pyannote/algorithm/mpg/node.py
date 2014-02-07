#!/usr/bin/env python
# encoding: utf-8

# Copyright 2012-2013 Herve BREDIN (bredin@limsi.fr)

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
from pyannote.base import URI, MODALITY, SEGMENT, TRACK, LABEL, IDENTITY
from collections import namedtuple


class IdentityNode(namedtuple('IdentityNode', ['identifier'])):

    def __new__(cls, identifier):
        return super(IdentityNode, cls).__new__(cls, identifier)

    def __get_modality(self):
        return IDENTITY
    modality = property(fget=__get_modality)

    def to_json(self):
        return {'kind': IDENTITY,
                LABEL: str(self.identifier)}

    def short(self):
        names = re.split('[ \-_]+', str(self.identifier))
        return "".join([name[0] for name in names[:-1]]) + "." + names[-1]


class TrackNode(namedtuple('TrackNode', [URI, MODALITY, SEGMENT, TRACK])):
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

    def __new__(cls, uri, modality, segment, track):
        return super(TrackNode, cls).__new__(cls, uri, modality,
                                                segment, track)

    def to_json(self):
        return {
            'kind': 'track',
            URI: str(self.uri),
            MODALITY: str(self.modality),
            SEGMENT: self.segment.to_json(),
            TRACK: str(self.track),
        }
