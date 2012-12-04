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
from pyannote.base.annotation import Annotation

class DirectTagger(BaseTagger):
    """
    Direct segment tagger
        
    **Timeline tagging.**
    Each segment in target timeline is tagged with all intersecting labels.
    
    """
    
    def __init__(self):
        super(DirectTagger, self).__init__(annotation=False, timeline=True)
    
    def _tag_timeline(self, source, timeline):
        """Timeline tagging
        
        Each segment in target `timeline` is tagged all intersecting labels.
        
        Parameters
        ----------
        source : Annotation
            Source annotation whose labels will be propagated
        timeline : Timeline
            Target timeline whose segments will be tagged.
        
        Returns
        -------
        tagged : Annotation
            Tagged `timeline`, one track per intersecting label
        
        """
        
        # initialize tagged timeline as an empty copy of source
        T = source.empty()
        
        # tag each segment of target timeline
        for segment in timeline:
            
            # extract the part of source annotation
            # intersecting current target segment
            t = source.crop(segment, mode='loose')
            
            for _, track, label in t.iterlabels():
                T[segment, T.new_track(segment, candidate=track)] = label
        
        return T

class ConservativeDirectTagger(BaseTagger):
    """
    Conservative direct segment tagger
    
    Only supports annotation tagging.
    
    
    """
    
    def __init__(self):
        super(ConservativeDirectTagger, self).__init__(annotation=True, \
                                                       timeline=False)
    
    def _tag_annotation(self, source, annotation):
        """Annotation tagging
        
        Parameters
        ----------
        source : Annotation
            Source annotation whose labels will be propagated
        annotation : Annotation
            Target annotation whose tracks will be tagged.
        
        Returns
        -------
        tagged : Annotation
            Tagged `annotation`.
        
        """
        
        # initialize tagged annotation as a copy of target annotation
        tagged = annotation.copy()
        
        # tag each segment of target annotation, one after the other
        for segment in tagged:
            
            # extract the part of source annotation
            # intersecting current target segment
            t = source.crop(segment, mode='loose')
            
            # if there is no intersecting segment
            # just skip to the next one
            if not t:
                continue
            
            # only tag segment 
            # when target has exactly one track and source only one
            # co-occurring label
                
            # don't do anything if target has more than one track
            tracks = tagged.tracks(segment)
            if len(tracks) > 1:
                continue
            else:
                track = tracks.pop()
            
            # don't do anything if source has more than one label
            labels = t.labels()
            if len(labels) > 1:
                continue
            else:
                label = labels[0]
            
            tagged[segment, track] = label
        
        return tagged


class ArgMaxDirectTagger(BaseTagger):
    """
    ArgMax direct segment tagger
    
    Parameters
    ----------
    unknown_last : bool
        If unknown_last is True, 
    
    It supports both timeline and annotation tagging.
    
    **Timeline tagging.**
    Each segment in target timeline is tagged with the `N` intersecting labels
    with greatest co-occurrence duration:
        - `N` is set to 1 in case source annotation is single-track. 
        - In case of a multi-track source, `N` is set to the the maximum number 
          of simultaneous tracks in intersecting source segments.
    
    **Annotation tagging.**
    
    """
    
    def __init__(self, known_first=False):
        super(ArgMaxDirectTagger, self).__init__(annotation=True, \
                                                 timeline=True)
        self.known_first = known_first
        
    def _tag_timeline(self, source, timeline):
        """Timeline tagging
        
        Each segment in target `timeline` is tagged with the `N` intersecting
        labels with greatest co-occurrence duration.
        `N` is set to the the maximum number of simultaneous tracks in 
        intersecting source segments.
        
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
        
        # track name
        n = 0
        
        # tag each segment of target timeline, one after the other
        for segment in timeline:
            
            # extract the part of source annotation
            # intersecting current target segment
            t = source.crop(segment, mode='loose')
            
            # if there is no intersecting segment
            # just skip to the next one
            if not t:
                continue
            
            # find largest number of co-occurring tracks ==> N
            # find N labels with greatest intersection duration
            # tag N tracks with those N labels
                
            # find largest number of simultaneous tracks (n_tracks)
            n_tracks = max([len(t.tracks(s)) for s in t])
                
            # find n_tracks labels with greatest intersection duration
            # and add them to the segment
            for i in range(n_tracks):
                    
                # find current best label
                label = t.argmax(segment, known_first=self.known_first)
                
                # if there is no label in stock
                # just stop tagging this segment
                if not label:
                    break
                # if current best label exists
                # create a new track and go for it.
                else:
                    T[segment, n] = label
                    n = n+1
                    t = t.subset(set([label]), invert=True)
            
        
        return T
    
    def _tag_annotation(self, source, annotation):
        """Annotation tagging
        
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
        
        # initialize tagged annotation as a copy of target annotation
        tagged = annotation.copy()
        
        # tag each segment of target annotation, one after the other
        for segment in tagged:
            
            # extract the part of source annotation
            # intersecting current target segment
            t = source.crop(segment, mode='loose')
            
            # if there is no intersecting segment
            # just skip to the next one
            if not t:
                continue
            
            # tag each track one after the other
            # always choose label with greatest intersection duration
            for track in tagged.tracks(segment):
                    
                # find current best label
                label = t.argmax(segment, known_first=self.known_first)
                    
                # if there is no label in stock
                # just stop tagging this segment
                if not label:
                    break
                    
                # if current best label exists, 
                # go for it and tag track
                else:
                    tagged[segment, track] = label
                    t = t.subset(set([label]), invert=True)
        
        return tagged


if __name__ == "__main__":
    import doctest
    doctest.testmod()
       