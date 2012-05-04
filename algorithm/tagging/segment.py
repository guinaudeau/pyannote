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

"""
Module ``pyannote.algorithm.tagging.segment`` provides segment-wise tagging algorithms. 
"""

from base import BaseTagger

class DirectTagger(BaseTagger):
    """
    Direct segment/track tagging based on intersecting tracks.
    
    Parameters
    ----------
    conflict : bool, optional
        In case 
        Defaults to False.
    
    
    
    
    
    
    By default (conflict=False), tagger quietly discards (do not tag) segments 
    where conflicts/uncertainties happen.
    Example of conflicts/uncertainties are:
    - multiple matching labels for a same segment/track couple
    - multiple matching tracks for a same segment in mono-track conditions
    When conflict=True, an error is raised when conflicts happen.
    """
    
    def __init__(self, conflict=False):
        super(DirectTagger, self).__init__(annotation=True, timeline=True)
        self.conflict = conflict
    
    def _tag_timeline(self, source, timeline):
        """
        
        Parameters
        ----------
        source : Annotation
            Source annotation whose labels will be propagated
        timeline : Timeline
            Target timeline whose segments will be tagged.
        
        Returns
        -------
        tagged : Annotation
            Tagged `timeline`
        
        """
        
        # initialize tagged timeline as an empty copy of source
        T = source.empty()
        
        # tag each segment of target timeline, one after the other
        for segment in timeline:
            
            # extract the part of source annotation
            # intersecting current target segment
            t = source(segment, mode='loose')
            
            # if source is multi-track
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
            
            # if source (and therefore tagged target) is single-track,
            # tag current target segment with greatest intersection duration
            else:
                # find label with greatest intersection
                label = t.argmax(segment)
                # if it exists, go for it!
                if label:
                    T[segment] = label
        
        return T
    
    def _tag_annotation(self, source, annotation):
        """
        
        Parameters
        ----------
        source : Annotation
            Source annotation whose labels will be propagated
        annotation : Annotation
            Target annotation whose tracks will be tagged.
        
        Returns
        -------
        tagged : Annotation
            Tagged `annotation`
        
        """
        
        
        new_target = annotation.copy()
        
        if new_target.multitrack:
            for segment in new_target:
                tracks = new_target[segment, :]
                if len(tracks) != 1:
                    if self.conflict:
                        raise ValueError('Segment %s has %d tracks.' \
                                         % (segment, len(tracks)))
                    else:
                        continue
                track = tracks.popitem()[0]
                possible_labels = set([])
                timeline = source.timeline(segment, mode='loose')
                for s in timeline:
                    possible_labels.update(source.get_labels(s))
                if len(possible_labels) == 1:
                    new_target[segment, track] = possible_labels.pop()
                else:
                    if self.conflict:
                        raise ValueError('Segment/track %s/%s has %d labels.' \
                              % (segment, track, len(possible_labels)))
        else:
            for segment in new_target:
                possible_labels = set([])
                timeline = source.timeline(segment, mode='loose')
                for s in timeline:
                    possible_labels.update(source.get_labels(s))
                if len(possible_labels) == 1:
                    new_target[segment] = possible_labels.pop()
                else:
                    if self.conflict:
                        raise ValueError('Segment %s has %d labels.' \
                              % (segment, len(possible_labels)))
        
        return new_target

if __name__ == "__main__":
    import doctest
    doctest.testmod()
       