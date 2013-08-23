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


from collections import namedtuple
from pyannote.base import URI, MODALITY, SEGMENT, TRACK, IDENTITY


class InstanceVertex(
    namedtuple('InstanceVertex', [SEGMENT, TRACK, MODALITY, URI])
):
    """Instance vertex

    Parameters
    ----------
    segment : Segment
        Segment
    track
        Track identifier
    modality : {'speaker', 'head', 'spoken', 'written'}
    uri
        Unique resource identifier

    """
    def __new__(cls, segment, track, modality=None, uri=None):
        return super(InstanceVertex, cls).__new__(
            cls, segment, track, modality, uri)

    def __str__(self):
        return '%s\n%s\n%s-%s' % (
            self.modality, self.uri, self.segment, self.track
        )


class IdentityVertex(namedtuple('IdentityVertex', [IDENTITY])):
    """Identity vertex

    Parameters
    ----------
    identity

    """
    def __new__(cls, identity):
        return super(IdentityVertex, cls).__new__(cls, identity)
