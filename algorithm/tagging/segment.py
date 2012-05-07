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
            Tagged `annotation`
        
        """
        
        # initialize tagged annotation as a copy of target annotation
        tagged = annotation.copy()
        
        # tag each segment of target annotation, one after the other
        for segment in tagged:
            
            # extract the part of source annotation
            # intersecting current target segment
            t = source(segment, mode='loose')
            
            # if there is no intersecting segment
            # just skip to the next one
            if not t:
                continue
            
            # if tagged annotation is multitrack, only tag segment 
            # when target has exactly one track and source only one
            # co-occurring label
            if tagged.multitrack:
                
                # don't do anything if target has more than one track
                tracks = set(tagged[segment, :])
                if len(tracks) > 1:
                    continue
                
                # don't do anything if source has more than one label
                labels = t.labels()
                if len(labels) > 1:
                    continue
                
                tagged[segment, tracks.pop()] = labels[0]
            
            # if tagged annotation is single-track, only tag segment
            # when source has exactly one co-occurring label
            else:
                
                # don't do anything if source has more than one label
                labels = t.labels()
                if len(labels) > 1:
                    continue
                
                tagged[segment] = labels[0]
        
        return tagged


class ArgMaxDirectTagger(BaseTagger):
    """
    ArgMax direct segment tagger
    
    It supports both timeline and annotation tagging.
    
    **Timeline tagging.**
    Each segment in target timeline is tagged with the `N` intersecting labels
    with greatest co-occurrence duration:
        - `N` is set to 1 in case source annotation is single-track. 
        - In case of a multi-track source, `N` is set to the the maximum number 
          of simultaneous tracks in intersecting source segments.
    
    **Annotation tagging.**
    
    """
    
    def __init__(self):
        super(ArgMaxDirectTagger, self).__init__(annotation=True, \
                                                 timeline=True)
    
    def _tag_timeline(self, source, timeline):
        """Timeline tagging
        
        Each segment in target `timeline` is tagged with the `N` intersecting
        labels with greatest co-occurrence duration:
            - `N` is set to 1 in case source annotation is single-track. 
            - In case of a multi-track source, `N` is set to the the maximum
              number of simultaneous tracks in intersecting source segments.
        
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
            
            # if there is no intersecting segment
            # just skip to the next one
            if not t:
                continue
            
            # if source is multi-track
            # find largest number of co-occurring tracks ==> N
            # find N labels with greatest intersection duration
            # tag N tracks with those N labels
            if T.multitrack:
                
                # find largest number of simultaneous tracks (n_tracks)
                n_tracks = max([len(t[s, :]) for s in t])
                
                # find n_tracks labels with greatest intersection duration
                # and add them to the segment
                for i in range(n_tracks):
                    
                    # find current best label
                    label = t.argmax(segment)
                    
                    # if there is no label in stock
                    # just stop tagging this segment
                    if not label:
                        break
                    # if current best label exists
                    # create a new track and go for it.
                    else:
                        T[segment, T.new_track(segment)] = label
                        t = t(label, invert=True)
            
            # if source is single-track,
            # tag current target segment with greatest intersection duration
            else:
                # find label with greatest intersection
                label = t.argmax(segment)
                # if it exists, go for it!
                if label:
                    T[segment] = label
        
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
            t = source(segment, mode='loose')
            
            # if there is no intersecting segment
            # just skip to the next one
            if not t:
                continue
            
            # if tagged annotation is multitrack
            # tag each track one after the other using argmax labels
            if tagged.multitrack:
                
                # tag each track one after the other
                # always choose label with greatest intersection duration
                for track in tagged[segment, :]:
                    
                    # find current best label
                    label = t.argmax(segment)
                    
                    # if there is no label in stock
                    # just stop tagging this segment
                    if not label:
                        break
                    
                    # if current best label exists, 
                    # go for it and tag track
                    else:
                        tagged[segment, track] = label
                        t = t(label, invert=True)
            
            # if tagged annotation is single-track
            # do the same (except there is only one track...)
            else:
                
                # find label with greatest intersection
                label = t.argmax(segment)
                # if it exists, go for it!
                if label:
                    tagged[segment] = label
        
        return tagged


if __name__ == "__main__":
    import doctest
    doctest.testmod()
       