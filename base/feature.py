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

class BaseFeature(object):
    
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
    video = property(fget=__get_video, \
                     fset=__set_video, \
                     fdel=None, \
                     doc="Processed video.")
    
    def __get_data(self): 
        return self.__data
    data = property(fget=__get_data, \
                    fset=None, \
                    fdel=None, \
                    doc="Raw features (numpy array).")
    
    def __get_toFrameRange(self): 
        return self.__toFrameRange
    def __set_toFrameRange(self, value): 
        self.__toFrameRange = value
    toFrameRange = property(fget=__get_toFrameRange, \
                            fset=__set_toFrameRange, \
                            fdel=None, \
                            doc="Segment to frame range conversion function.")
    
    def __get_toSegment(self): 
        return self.__toSegment
    def __set_toSegment(self, value):
        self.__toSegment = value
    toSegment = property(fget=__get_toSegment, \
                         fset=__set_toSegment, \
                         fdel=None, \
                         doc="Frame range to segment conversion function.")
    
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

    def __getitem__(self, key):
        if isinstance(key, int):
            return np.take(self.data, [key], axis=0, out=None, mode='raise')
        elif isinstance(key, slice):
            return np.take(self.data, \
                           range(key.start, key.stop, key.step \
                                                      if key.step else 1), \
                           axis=0, out=None, mode='raise')
        else:
            raise TypeError('')
    
    def extent(self):
        N, D = self.data.shape
        return self.toSegment(0, N)
    

class SlidingWindow(object):
    """
    >>> sw = SlidingWindow(duration, step, start)    
    >>> frame_range = (a, b)
    >>> frame_range == sw.toFrameRange(sw.toSegment(*frame_range))
    ... True
    
    >>> segment = Segment(A, B)
    >>> new_segment = sw.toSegment(*sw.toFrameRange(segment))
    >>> abs(segment) - abs(segment & new_segment) < .5 * sw.step
    
    """
    def __init__(self, duration=0.030, step=0.010, start=0.000, end=None):
        super(SlidingWindow, self).__init__()
        self.__duration = duration
        self.__step = step
        self.__start = start
        self.__end = end
    
    def __get_start(self): 
        return self.__start
    def __set_start(self, value):
        self.__start = value
    start = property(fget=__get_start, \
                     fset=__set_start, \
                     fdel=None, \
                     doc="Sliding window start time in seconds.")

    def __get_end(self): 
        return self.__end
    def __set_end(self, value):
        self.__end = value
    end = property(fget=__get_end, \
                     fset=__set_end, \
                     fdel=None, \
                     doc="Sliding window end time in seconds.")

    def __get_step(self): 
        return self.__step
    def __set_step(self, value):
        self.__step = value
    step = property(fget=__get_step, \
                    fset=__set_step, \
                    fdel=None, \
                    doc="Sliding window step in seconds.")

    def __get_duration(self): 
        return self.__duration
    def __set_duration(self, value):
        self.__duration = value
    duration = property(fget=__get_duration, \
                        fset=__set_duration, \
                        fdel=None, \
                        doc="Sliding window duration in seconds.")

    def __closest_frame(self, t):
        """
        Finds index of closest frame to timestamp t
        """
        frame = np.rint(.5 + (t - self.start - .5*self.duration) / self.step)
        return int(frame)
    
    def toFrameRange(self, segment):
        """
        Segment to 0-indexed frame range
        """
        # find closest frame to segment start
        i0 = self.__closest_frame(segment.start)
        # find closest frame to segment end
        j0 = self.__closest_frame(segment.end)
        # return frame range as (start_frame, number_of_frame) tuple
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
        
    def __iter__(self):
        
        if self.end is None:
            raise ValueError('Please set end time first.')
        extent = Segment(start=self.start, end=self.end)  

        position = 0
        while(True):
            start = self.start + position * self.step
            end   = start + self.duration
            window = extent & Segment(start=start, end=end)
            if window:
                yield window
                position += 1
            else:
                break
        
class SlidingWindowFeature(BaseFeature):
    
    def __init__(self, data, sliding_window, video=None):
        
        sw = sliding_window
        super(SlidingWindowFeature, self).__init__(data, sw.toFrameRange, \
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
  