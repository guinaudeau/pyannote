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

Features.

"""

import numpy as np
from pyannote.base.segment import Segment, SlidingWindow
from pyannote.base.timeline import Timeline

class BaseSegmentFeature(object):
    """
    Base class for any segment/feature iterator.    
    """
    def __init__(self, video=None):
        super(BaseSegmentFeature, self).__init__()
        self.__video = video
    
    def __get_video(self): 
        return self.__video
    def __set_video(self, value):
        self.__video = value
    video = property(fget=__get_video, fset=__set_video)
    """Path to (or any identifier of) described video"""
    
    def __iter__(self):
        """Segment/feature vector iterator
        
        Use expression 'for segment, feature_vector in segment_feature'
        
        This method must be implemented by subclass.
        
        """
        raise NotImplementedError('Missing method "__iter__".')
 
class BasePrecomputedSegmentFeature(BaseSegmentFeature):
    """'Segment iterator'-driven precomputed feature iterator.
    
    Parameters
    ----------
    data : numpy array
        Feature vectors stored in such a way that data[i] is ith feature vector.
    segment_iterator : :class:`SlidingWindow` or :class:`Timeline`
        Segment iterator.
        Its length must correspond to `data` length.
    video : string, optional
        name of (audio or video) described document
    
    """
    def __init__(self, data, segment_iterator, video=None):
        # make sure data does not contain NaN nor inf
        data = np.asarray_chkfinite(data)
                
        # make sure segment_iterator is actually one of those
        if not isinstance(segment_iterator, (SlidingWindow, Timeline)):
            raise TypeError("segment_iterator must 'Timeline' or "
                            "'SlidingWindow'.")
        
        # make sure it iterates the correct number of segments
        try:
            N = len(segment_iterator)
        except Exception, e:
            # an exception is raised by `len(sliding_window)`
            # in case sliding window has infinite end.
            # this is acceptable, no worry...
            pass
        else:
            n = data.shape[0]
            if n != N:
                raise ValueError("mismatch between number of segments (%d) "
                                 "and number of feature vectors (%d)." % (N, n))
        
        super(BasePrecomputedSegmentFeature, self).__init__(video=video)
        self.__data = data
        self.__segment_iterator = segment_iterator
    
    def __get_data(self): 
        return self.__data
    data = property(fget=__get_data)
    """Raw feature data (numpy array)"""

    def __iter__(self):
        """Feature vector iterator
        
        Use expression 'for segment, feature_vector in periodic_feature'
        
        """
        
        # get number of feature vectors 
        n = self.__data.shape[0]
        
        for i, segment in enumerate(self.__segment_iterator):
            
            # make sure we do not iterate too far...
            if i >= n:
                break
            
            # yield current segment and corresponding feature vector
            yield segment, self.__data[i]
    
    def _segmentToRange(self, segment):
        """
        Parameters
        ----------
        segment : :class:`pyannote.base.segment.Segment`
        
        Returns
        -------
        i, n : int
        
        """
        raise NotImplementedError('Missing method "_segmentToRange".')
    
    def _rangeToSegment(self, i, n):
        """
        Parameters
        ----------
        i, n : int
        
        Returns
        -------
        segment : :class:`pyannote.base.segment.Segment`
        
        """
        raise NotImplementedError('Missing method "_rangeToSegment".')
        
    def __call__(self, subset, mode='loose'):
        """
        Use expression 'feature(subset)'
        
        Parameters
        ----------
        subset : :class:`pyannote.base.segment.Segment` or 
                 :class:`pyannote.base.timeline.Timeline`
        
        Returns
        -------
        data : numpy array
        
        """
    
        if not isinstance(subset, (Segment, Timeline)):
            raise TypeError('')
        
        if isinstance(subset, Segment):
            i, n = self._segmentToRange(subset)
            indices = range(i, i+n)
        
        elif isinstance(subset, Timeline):
            indices = []
            for segment in subset.coverage():
                i, n = self._segmentToRange(segment)
                indices += range(i, i+n)
                
        return np.take(self.__data, indices, axis=0, out=None, mode='clip')
    
class PeriodicPrecomputedFeature(BasePrecomputedSegmentFeature):
    """'Sliding window'-driven precomputed feature iterator.
    
    Parameters
    ----------
    data : numpy array
        Feature vectors stored in such a way that data[i] is ith feature vector.
    sliding_window : :class:`SlidingWindow`
        Sliding window. Its length must correspond to `data` length
        (or it can be infinite -- ie. sliding_window.end = None)
    video : string, optional
        name of (audio or video) described document
    
    Examples
    --------
        >>> data = ...
        >>> sliding_window = SlidingWindow( ... )
        >>> feature_iterator = PeriodicPrecomputedFeature(data, sliding_window)
        >>> for segment, feature_vector in feature_iterator:
        ...     pass
        
    """
    
    def __init__(self, data, sliding_window, video=None):
        
        super(PeriodicPrecomputedFeature, self).__init__(data, sliding_window, \
                                                         video=video)
        
    def _segmentToRange(self, segment):
        """
        Parameters
        ----------
        segment : :class:`pyannote.base.segment.Segment`
        
        Returns
        -------
        i, n : int
        
        """
        return self.__sliding_window.segmentToRange(segment)
    
    def _rangeToSegment(self, i, n):
        """
        Parameters
        ----------
        i, n : int
        
        Returns
        -------
        segment : :class:`pyannote.base.segment.Segment`
        
        """
        return self.__sliding_window.rangeToSegment(i, n)        

class TimelinePrecomputedFeature(BasePrecomputedSegmentFeature):
    """Timeline-driven precomputed feature iterator.
    
    Parameters
    ----------
    data : numpy array
        Feature vectors stored in such a way that data[i] is ith feature vector.
    timeline : :class:`Timeline`
        Timeline whose length must correspond to `data` length
    video : string, optional
        name of (audio or video) described document
    
    Examples
    --------
        >>> data = ...
        >>> timeline = Timeline( ... )
        >>> feature_iterator = TimelinePrecomputedFeature(data, timeline)
        >>> for segment, feature_vector in feature_iterator:
        ...     pass
    
    
    """
    
    def __init__(self, data, timeline, video=None):  
        super(TimelinePrecomputedFeature, self).__init__(data, timeline, \
                                                         video=video)
        
    def _segmentToRange(self, segment):
        timeline = self.__timeline(segment, mode='loose')
        if timeline:
            # index of first segment in sub-timeline
            first_segment = timeline[0]
            i = self.__timeline.index(first_segment)
            # number of segments in sub-timeline
            n = len(timeline)
        else:
            i = 0
            n = 0

        return i, n
        
    def _rangeToSegment(self, i, n):
        first_segment = self.__timeline[i]
        last_segment = self.__timeline[i+n]
        return first_segment | last_segment    

if __name__ == "__main__":
    import doctest
    doctest.testmod()
