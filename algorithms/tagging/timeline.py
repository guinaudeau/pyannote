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

from base import BaseTimelineTagger

class ConservativeTimelineTagger(BaseTimelineTagger):
    def __init__(self):
        super(ConservativeTimelineTagger, self).__init__()
    
    def tag(self, source, target):
        
        T = source.empty()
        
        for segment in target:
            # extract intersecting segments
            t = source(segment, mode='loose')
            if source.multitrack:
                # -- multi-track
                tracks = {}
                for src_segment in t:
                    for track, label in t[src_segment, :].iteritems():
                        if track not in tracks:
                            tracks[track] = set([])
                        tracks[track].add(label)
                for track in tracks:
                    labels = tracks[track]
                    if len(labels) == 1:
                        T[segment, track] = labels.pop()
                    elif len(labels) > 1:
                        # pass
                        print '2+ labels for %s/%s' % (segment, track)
                        # raise ValueError('2+ labels for %s/%s' \
                        #                  % (segment, track))
                    else:
                        pass
            else:
                # -- mono-track
                labels = t.IDs
                if len(labels) == 1:
                    T[segment] = labels[0]
                elif len(labels) > 1:
                    raise ValueError('2+ labels for %s.' % segment)
                else:
                    pass
        
        return T