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

from pyannote.base.timeline import Timeline

class BaseTimelineParser(object):
    def __init__(self):
        super(BaseTimelineParser, self).__init__()
        
        # (video, modality) ==> timeline
        self.__loaded = {}
    
    def __get_videos(self):
        return sorted(self.__loaded)
    videos = property(fget=__get_videos)
    """"""
    
    def _add(self, segment, video):
        if video not in self.__loaded:
            self.__loaded[video] = Timeline(video=video)
        self.__loaded[video] += segment
    
    def read(self, path):
        raise NotImplementedError('')
    
    def __call__(self, video=None):
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
    
    def read(self, path, video=None):
        
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
        

from pyannote.base.annotation import Annotation

class BaseAnnotationParser(object):
    def __init__(self, multitrack):
        super(BaseAnnotationParser, self).__init__()
        self.__multitrack = multitrack
        self.__loaded = {}

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
            self.__loaded[key][segment, track] = label
        else:
            self.__loaded[key][segment] = label
    
    def __call__(self, video=None, modality=None):
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
            # empty annotation
            return Annotation(video=video, modality=modality)
        elif len(match) == 1:
            return match.values()[0]
        else:
            raise ValueError('')


class BaseTextualAnnotationParser(BaseAnnotationParser):
    def __init__(self, multitrack):
        super(BaseTextualAnnotationParser, self).__init__(multitrack)
    
    def _comment(self, line):
        raise NotImplementedError('')
    
    def _parse(self, line):
        raise NotImplementedError('')
    
    def read(self, path, video=None, modality=None):
        
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
            if m is None:
                m = modality
            
            # add label
            self._add(s, t, l, v, m)
            
        fp.close()


import numpy as np
from pyannote.base.feature import PeriodicPrecomputedFeature

class BasePeriodicFeatureParser(object):
    
    def __init__(self):
        super(BasePeriodicFeatureParser, self).__init__()
    
    def _read_header(self, fp):
        """
        Read the header of a binary file.
        
        Parameters
        ----------
        fp : file
        
        Returns
        -------
        dtype : 
            Feature vector type
        sliding_window : :class:`pyannote.base.segment.SlidingWindow`
            
        count : 
            Number of feature vectors
        
        """
        raise NotImplementedError('')
    
    def _read_data(self, fp, dtype, count=-1):
        """
        Construct an array from data in a binary file.
        
        Parameters
        ----------
        file : file
            Open file object
        dtype : data-type
            Data type of the returned array.
            Used to determine the size and byte-order of the items in the file.
        count : int
            Number of items to read. ``-1`` means all items (i.e., the complete
            file).
            
        Returns
        -------
        
        """
        raise NotImplementedError('')
        
    def read(self, path, video=None):
        """
        
        Parameters
        ----------
        path : str
            path to binary feature file
        video : str, optional
        
        Returns
        -------
        feature : :class:`pyannote.base.feature.PeriodicPrecomputedFeature`
            
        
        """
        
        # open binary file
        fp = open(path, 'rb')
        # read header
        dtype, sliding_window, count = self._read_header(fp)
        # read data
        data = self._read_data(fp, dtype, count=count)
        
        # if `video` is not provided, use `path` instead
        if video is None:
            video = str(path)
        
        # create feature object
        feature =  PeriodicPrecomputedFeature(data, sliding_window, 
                                              video=video)
        # close binary file
        fp.close()
        
        return feature

class BaseBinaryPeriodicFeatureParser(BasePeriodicFeatureParser):
    
    """
    Base class for periodic feature stored in binary format.
    """
    
    def __init__(self):
        super(BaseBinaryPeriodicFeatureParser, self).__init__()
        
    def _read_data(self, fp, dtype, count=-1):
        """
        Construct an array from data in a binary file.
        
        Parameters
        ----------
        file : file
            Open file object
        dtype : data-type
            Data type of the returned array.
            Used to determine the size and byte-order of the items in the file.
        count : int
            Number of items to read. ``-1`` means all items (i.e., the complete
            file).
            
        Returns
        -------
        
        """
        return np.fromfile(fp, dtype=dtype, sep='', count=count)

class BaseTextualPeriodicFeatureParser(BasePeriodicFeatureParser):
    
    def __init__(self):
        super(BaseTextualPeriodicFeatureParser, self).__init__()
    
    def _read_data(self, fp, dtype, count=-1):
        raise NotImplementedError('')

if __name__ == "__main__":
    import doctest
    doctest.testmod()

