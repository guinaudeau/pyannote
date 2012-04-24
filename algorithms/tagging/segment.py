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

from base import BaseTagger

class ConservativeSegmentTagger(BaseTagger):

    def __init__(self):
        super(ConservativeSegmentTagger, self).__init__()
    
    def tag(self, source, target):
        
        new_target = target.copy()
        
        if new_target.multitrack:
            for segment in new_target:
                tracks = new_target[segment, :]
                if len(tracks) != 1:
                    continue
                track = tracks.popitem()[0]
                possible_labels = set([])
                timeline = source.timeline(segment, mode='loose')
                for s in timeline:
                    possible_labels.update(source.ids(s))
                if len(possible_labels) == 1:
                    new_target[segment, track] = possible_labels.pop()
        else:
            for segment in new_target:
                possible_labels = set([])
                timeline = source.timeline(segment, mode='loose')
                for s in timeline:
                    possible_labels.update(source.ids(s))
                if len(possible_labels) == 1:
                    new_target[segment] = possible_labels.pop()
        
        return new_target
