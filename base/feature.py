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

import numpy as np
from segment import Segment
from timeline import Timeline

class Feature(object):
    """
    """
    def __init__(self, data, \
                       toFrameRange_func, \
                       toSegment_func, \
                       video=None):
        
        super(Feature, self).__init__()
        self._data = data
        self._toFrameRange_func = toFrameRange_func
        self._toSegment_func    = toSegment_func
        self._video = video
    
    # --------------- #
    # Getters/Setters #
    # --------------- #
    
    def _get_video(self): 
        return self._video
    def _set_video(self, value):
        self._video = value
    video = property(fget=_get_video, fset=_set_video, fdel=None, doc="Processed video.")
    
    def _get_data(self): 
        return self._data
    data = property(fget=_get_data, fset=None, fdel=None, doc="Raw features (numpy array).")
    
    def _get_toFrameRange(self): 
        return self._toFrameRange_func
    toFrameRange = property(fget=_get_toFrameRange, fset=None, fdel=None, \
                            doc="Segment to frame range conversion function.")
    
    def _get_toSegment(self): 
        return self._toSegment_func
    toSegment = property(fget=_get_toSegment, fset=None, fdel=None, \
                            doc="Frame range to segment conversion function.")
    
    def __getitem__(self, key):
        if isinstance(key, Segment):
            i0, n = self._toFrameRange_func(key)
            return np.take(self._data, \
                           range(i0, i0+n), \
                           axis=0, \
                           out=None, \
                           mode='raise')
        elif isinstance(key, Timeline):
            # make sure there is no overlapping segment
            coverage = key.coverage()
            indices = []
            for s, segment in enumerate(coverage):
                i0, n = self._toFrameRange_func(segment)
                indices += range(i0, i0+n)
            return np.take(self._data, \
                           indices, \
                           axis=0, \
                           out=None, \
                           mode='raise')
        elif isinstance(key, slice):
            return np.take(self._data, \
                           range(key.start, key.stop, key.step if key.step else 1), \
                           axis=0, \
                           out=None, \
                           mode='raise')
        elif isinstance(key, int):
            return np.take(self._data, \
                           [key], \
                           axis=0,
                           out=None,
                           mode='raise')
        else:
            raise TypeError('Cannot get anything but Segment or slice of Feature')
    
    def extent(self):
        n_features = self._data.shape[0]
        return self._toSegment_func(0, n_features)
    

class SlidingWindow(object):
    """
    > sw = SlidingWindow(duration, step, start)    
    > frame_range = (a, b)
    > frame_range == sw.toFrameRange(sw.toSegment(*frame_range))
    
    > segment = Segment(A, B)
    > new_segment = sw.toSegment(*sw.toFrameRange(segment))
    > abs(segment) - abs(segment & new_segment) < .5 * sw.step
    
    """
    def __init__(self, duration=0.030, step=0.010, start=0.000):
        super(SlidingWindow, self).__init__()
        self._duration = duration
        self._step = step
        self._start = start
    
    def get_start(self): 
        return self._start
    def set_start(self, value):
        self._start = value
    start = property(fget=get_start, fset=set_start, fdel=None, doc="Sliding window start time in seconds.")
    
    def get_duration(self): 
        return self._duration
    def set_duration(self, value):
        self._duration = value
    duration = property(fget=get_duration, fset=set_duration, fdel=None, doc="Sliding window duration in seconds.")

    def get_step(self): 
        return self._step
    def set_step(self, value):
        self._step = value
    step = property(fget=get_step, fset=set_step, fdel=None, doc="Sliding window step in seconds.")
    
    def toFrameRange(self, segment):
        """
        Segment to 0-indexed frame range
        """
        
        # find frame center is the closest to the segment start
        i0 = int(np.rint(.5 + (segment.start-self.start-.5*self.duration) / self.step))
        # find frame whose center is the closest to the segment end
        j0 = int(np.rint(.5 + (segment.stop -self.start-.5*self.duration) / self.step))
        
        i0 = max(0, i0)
        n = j0 - i0
        return i0, n
    
    def toSegment(self, i0, n):
        """
        i0: 0-indexed frame number
        n: number of frames
        
        Each frame represents a unique segment of duration 'step', 
        centered on the middle of the frame
        
        The very first frame (i0 == 0) is the exception.
        It is extended to the left so that it also represents the very beginning of the file
        """
        
        # frame start time
        # start = self.start + i0 * self.step
        # frame middle time
        # start += .5 * self.duration
        # subframe start time
        # start -= .5 * self.step
        start = self.start + (i0-.5) * self.step + .5 * self.duration
        duration = n * self.step
        segment = Segment(start, start + duration)
        
        if i0 == 0:
            # extend segment to the beginning of the timeline
            delta = segment.start - self.start
            segment = (delta << segment)
        
        return segment


class SlidingWindowFeature(Feature):
    def __init__(self, data, \
                       sliding_window=SlidingWindow(), \
                       video=None):
        super(SlidingWindowFeature, self).__init__(data, sliding_window.toFrameRange, \
                                                         sliding_window.toSegment, \
                                                   video=video)
        self._sliding_window = sliding_window
        
    def _get_sw(self): 
        return self._sliding_window
    sliding_window = property(fget=_get_sw, fset=None, fdel=None, \
                              doc="Sliding window on which features are extracted.")

class TimelineFeature(Feature):
    def __init__(self, data, \
                       timeline=Timeline(), \
                       video=None):
        
        def _local_toFrameRange(segment):
            segments = timeline[segment]
            i0 = timeline.index(segments[0])
            n = len(segments)
            return i0, n
        
        def _local_toSegment(i0, n):
            raise NotImplementedError('toSegment is not implemented for TimelineFeature')
        
        super(TimelineFeature, self).__init__(data, _local_toFrameRange, \
                                                    _local_toSegment, \
                                                    video=video)
        self._timeline = timeline
    
    def _get_tl(self): 
        return self.timeline
    timeline = property(fget=_get_tl, fset=None, fdel=None, \
                              doc="Timeline on which features are aligned (one per segment).")
    
    