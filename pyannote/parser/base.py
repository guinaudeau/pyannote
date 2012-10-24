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

import sys
from pyannote.base.timeline import Timeline

class BaseTimelineParser(object):
    def __init__(self):
        super(BaseTimelineParser, self).__init__()
        
        # (video, modality) ==> timeline
        self.reset()
    
    def __get_videos(self):
        return sorted(self.__loaded)
    videos = property(fget=__get_videos)
    """"""
    
    def _add(self, segment, video):
        if video not in self.__loaded:
            self.__loaded[video] = Timeline(video=video)
        self.__loaded[video] += segment
    
    def reset(self):
        self.__loaded = {}
    
    def read(self, path, video=None, **kwargs):
        raise NotImplementedError('')
    
    def __call__(self, video=None, **kwargs):
        """
        
        Parameters
        ----------
        video : str, optional
            If None and there is more than one video 
        
        Returns
        -------
        timeline : :class:`pyannote.base.timeline.Timeline`
        
        """
        
        match = dict(self.__loaded)
        
        # filter out all timelines 
        # but the ones for the requested video
        if video is not None:
            match = {v: timeline for v, timeline in match.iteritems()
                                 if v == video }
        
        if len(match) == 0:
            # empty annotation
            return Timeline(video=video)
        elif len(match) == 1:
            return match.values()[0]
        else:
            raise ValueError('')

class BaseTextualTimelineParser(BaseTimelineParser):
    
    def __init__(self):
        super(BaseTextualTimelineParser, self).__init__()
    
    def _comment(self, line):
        raise NotImplementedError('')
    
    def _parse(self, line):
        raise NotImplementedError('')
    
    def read(self, path, video=None, **kwargs):
        
        # default video to path
        if video is None:
            video = path
        
        # open file and loop on each line
        fp = open(path, 'r')
        for line in fp:
            
            # strip line
            line = line.strip()
            
            # comment ?
            if self._comment(line):
                continue
            
            # parse current line
            s, v = self._parse(line)
            
            # found video ?
            if v is None:
                v = video
                
            # add segment
            self._add(s, v)
            
        fp.close()
        
        return self
    
    def write(self, timeline, f=sys.stdout, video=None):
        """
        
        Parameters
        ----------
        timeline : :class:`pyannote.base.timeline.Timeline`
            Timeline
        f : file or str, optional
            Default is stdout.
        video : str, optional
            When provided, overrides `timeline` video attribute.
        """
        
        if video is None:
            video = timeline.video
        
        if isinstance(f, file):
            self._append(timeline, f, video)
        else:
            f = open(f, 'w')
            self._append(timeline, f, video)
            f.close()


from pyannote.base.annotation import Annotation, Unknown

class BaseAnnotationParser(object):
    def __init__(self, multitrack):
        super(BaseAnnotationParser, self).__init__()
        self.__multitrack = multitrack
        self.reset()

    def __get_videos(self):
        return sorted(set([v for (v, m) in self.__loaded]))
    videos = property(fget=__get_videos)
    """"""
    
    def __get_modalities(self):
        return sorted(set([m for (v, m) in self.__loaded]))
    modalities = property(fget=__get_modalities)
    """"""
    
    def _add(self, segment, track, label, video, modality):
        key = (video, modality)
        if key not in self.__loaded:
            self.__loaded[key] = Annotation(video=video, modality=modality,
                                            multitrack=self.__multitrack)
        if self.__multitrack:
            if track is None:
                track = self.__loaded[key].new_track(segment)
            self.__loaded[key][segment, track] = label
        else:
            self.__loaded[key][segment] = label
    
    def reset(self):
        self.__loaded = {}
    
    def read(self, path, video=None, modality=None, **kwargs):
        raise NotImplementedError('')
    
    def __call__(self, video=None, modality=None, **kwargs):
        """
        
        Parameters
        ----------
        video : str, optional
            If None and there is more than one video 
        modality : str, optional
        
        Returns
        -------
        annotation : :class:`pyannote.base.annotation.Annotation`
        
        """
        
        match = dict(self.__loaded)
        
        # filter out all annotations 
        # but the ones for the requested video
        if video is not None:
            match = {(v, m): ann for (v, m), ann in match.iteritems()
                                 if v == video }
        
        # filter out all remaining annotations 
        # but the ones for the requested modality
        if modality is not None:
            match = {(v, m): ann for (v, m), ann in match.iteritems()
                                 if m == modality}
        
        if len(match) == 0:
            A = Annotation(video=video, modality=modality)
        elif len(match) == 1:
            A = match.values()[0]
        else:
            raise ValueError('Found more than one matching annotation: %s' % match.keys())
        
        # make sure UnknownXXXX labels are changed into Unknown objects
        labels = A.labels()
        translation = {l: Unknown() for l in A.labels() 
                                    if isinstance(l, str) and l[:7]=='Unknown'}
        
        return A % translation

class BaseTextualAnnotationParser(BaseAnnotationParser):
    def __init__(self, multitrack):
        super(BaseTextualAnnotationParser, self).__init__(multitrack)
    
    def _comment(self, line):
        raise NotImplementedError('')
    
    def _parse(self, line):
        raise NotImplementedError('')
    
    def read(self, path, video=None, modality=None, **kwargs):
        
        # default video to path
        if video is None:
            video = path
        
        # open file and loop on each line
        fp = open(path, 'r')
        for line in fp:
            
            # strip line
            line = line.strip()
            
            # comment ?
            if self._comment(line):
                continue
            
            # parse current line
            s, t, l, v, m = self._parse(line)
            
            # found video ?
            if v is None:
                v = video
            
            # found modality ?
            if m is None or m == 'None':
                m = modality
            
            # add label
            self._add(s, t, l, v, m)
            
        fp.close()
        
        return self
    
    def _append(self, annotation, f, video, modality):
        raise NotImplementedError('')
    
    def write(self, annotation, f=sys.stdout, video=None, modality=None):
        """
        
        Parameters
        ----------
        annotation : :class:`pyannote.base.annotation.Annotation`
            Annotation
        f : file or str, optional
            Default is stdout.
        video : str, optional
            When provided, overrides `annotation` video attribute.
        modality : str, optional
            When provided, overrides `annotation` modality attribute.
        """
        
        if video is None:
            video = annotation.video
        if modality is None:
            modality = annotation.modality
        
        if isinstance(f, file):
            self._append(annotation, f, video, modality)
            f.flush()
        else:
            f = open(f, 'w')
            self._append(annotation, f, video, modality)
            f.close()


if __name__ == "__main__":
    import doctest
    doctest.testmod()

