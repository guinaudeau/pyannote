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

"""

import numpy as np
from pyannote.base.segment import Segment
from pyannote.base.timeline import Timeline

class BaseFeature(object):
    """
    
    Parameters
    ----------
    data : numpy array
    
    toFrameRange : func
    
    toSegment : func
    
    video : string, optional
        name of (audio or video) described document
    
    """
    def __init__(self, data, toFrameRange, toSegment, video=None):
        super(BaseFeature, self).__init__()
        self.__data = data
        self.__toFrameRange = toFrameRange
        self.__toSegment = toSegment
        self.__video = video
    
    def __get_video(self): 
        return self.__video
    def __set_video(self, value):
        self.__video = value
    video = property(fget=__get_video, fset=__set_video)
    """Path to (or any identifier of) described video"""
    
    def __get_data(self): 
        return np.array(self.__data)
    data = property(fget=__get_data)
    """Raw feature data (numpy array)"""
    
    def __get_toFrameRange(self): 
        return self.__toFrameRange
    def __set_toFrameRange(self, value): 
        self.__toFrameRange = value
    toFrameRange = property(fget=__get_toFrameRange, fset=__set_toFrameRange)
    """Segment to frame range conversion function."""
    
    def __get_toSegment(self): 
        return self.__toSegment
    def __set_toSegment(self, value):
        self.__toSegment = value
    toSegment = property(fget=__get_toSegment, fset=__set_toSegment)
    """Frame range to segment conversion function."""
    
    def __call__(self, subset, mode='loose'):
        """Use expression "feature(subset, mode='strict')"
        
        Parameters
        ----------
        subset : Segment or Timeline
        
        mode : {'strict', 'loose'}
            Default `mode` is 'losse'.
        
        Returns
        -------
        data : numpy array
            In 'strict' mode, `data` only contains features for segments that
            are fully included in provided segment or timeline coverage.
            In 'loose' mode, `data` contains features for every segment
            intersecting provided segment or timeline.
        
        Examples
        --------
        
        """
    
    
    
    
    
    def __call__(self, subset):
        
        # extract segment feature vectors
        if isinstance(subset, Segment):
            
            # get frame range corresponding to the segment
            i0, n = self.toFrameRange(subset)
            
            # perform the actual extraction
            return np.take(self.data, range(i0, i0+n), axis=0, \
                           out=None, mode='clip')
        
        # extract timeline feature vectors
        elif isinstance(subset, Timeline):
            
            # provided timeline has to be a partition
            # ie must not contain any overlapping segments
            if subset < 0:
                raise ValueError('Overlapping segments.')
                
            # concatenate frame ranges of all segments
            indices = []
            for segment in subset.coverage():
                i0, n = self.toFrameRange(segment)
                indices += range(i0, i0+n)
            
            # perform the actual extraction
            return np.take(self.data, indices, axis=0, out=None, mode='raise')
        
        else:
            raise TypeError('')
    
    # def __getitem__(self, key):
    #     if isinstance(key, int):
    #         return np.take(self.data, [key], axis=0, out=None, mode='raise')
    #     elif isinstance(key, slice):
    #         return np.take(self.data, \
    #                        range(key.start, key.stop, key.step \
    #                                                   if key.step else 1), \
    #                        axis=0, out=None, mode='raise')
    #     else:
    #         raise TypeError('')
    
    # def extent(self):
    #     N, D = self.data.shape
    #     return self.toSegment(0, N)

class PeriodicFeature(BaseFeature):
    
    def __init__(self, data, sliding_window, video=None):
        
        sw = sliding_window
        super(PeriodicFeature, self).__init__(data, sw.toFrameRange, \
                                                   sw.toSegment, video=video)
        self.__sliding_window = sw
        
    def __get_sliding_window(self): 
        return self.__sliding_window
    sliding_window = property(fget=__get_sliding_window, \
                              fset=None, \
                              fdel=None, \
                              doc="Feature extraction sliding window.")

class TimelineFeature(BaseFeature):
    
    def __init__(self, data, timeline, video=None):        
        super(TimelineFeature, self).__init__(data, None, None, video=video)
        self.__timeline = timeline
        self.toFrameRange = self.__toFrameRange
        self.toSegment = self.__toSegment
        
    def __get_timeline(self): 
        return self.__timeline
    timeline = property(fget=__get_timeline, \
                        fset=None, \
                        fdel=None, \
                        doc="Feature extraction timeline.")
    
    def __toFrameRange(self, segment):
        sub_timeline = self.timeline(segment, mode='loose')
        if sub_timeline:
            # index of first segment in sub-timeline
            i0 = self.timeline.index( sub_timeline[0] )
            # number of segments in sub-timeline
            n = len(sub_timeline)
            return i0, n
        else:
            return 0, 0
        
    def __toSegment(self, i0, n):
        raise NotImplementedError('')
        # first_segment = self.timeline[i0]
        # last_segment = self.timeline[i0+n]
        return first_segment | last_segment


if __name__ == "__main__":
    import doctest
    doctest.testmod()
