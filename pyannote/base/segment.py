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

SEGMENT_PRECISION = 1e-6

class Segment(object):
    """
    Temporal interval defined by its `start` and `end` times.
    
    Multiple segment operators are available -- including intersection (&),
    inclusion (in), emptiness test, start/end time shifting (+, -, >>, <<). 
    They are illustrated in **Examples** section.
    
    Comparison of two segments is also available (==, !=, <, <=, >, >=). 
    Two segments are equal iff they have identical start and end times.
    Segment S is smaller than segment T iff S.start < T.start or if they have
    the same start time and S.end < T.start.
    
    Parameters
    ----------
    start, end : float, optional
        `start` and `end` times, in seconds (the default is 0).
    
    Returns
    -------
    segment : Segment
        New segment with `start` and `end` times.
    
    Examples
    --------
    Create a new temporal interval between 00:13.000 and 00:37.000.

        >>> segment = Segment(start=13., end=37)
        >>> print segment
        [13 --> 37]
    
    Inclusion, intersection, union & gap
    
        >>> s1 = Segment(1, 2)
        >>> s2 = Segment(0, 3)
        >>> if s1 in s2:
        ...    print "Segment %s is included in segment %s." % (s1, s2)
        Segment [1 --> 2] is included in segment [0 --> 3].
        >>> s3 = Segment(2, 5)
        >>> print s1 & s3
        ∅
        >>> print s2 & s3
        [2 --> 3]
        >>> print s2 | s3
        [0 --> 5]
        >>> print s1 ^ Segment(5, 7)
        [2 --> 5]

    Test whether segment is empty or not.
    
        >>> if not Segment(10, 10):
        ...    print "Segment is empty."
        Segment is empty.
    
    Start & end time shifting
    
        >>> s = Segment(3, 4)
        >>> print s + 3
        [6 --> 7]
        >>> print s >> 3
        [3 --> 7]
        >>> print s << 0.5
        [3 --> 3.5]
        >>> print 2 << s >> 0.5
        [1 --> 4.5]
    
    Comparison
    
        >>> s1 = Segment(1, 3)
        >>> s2 = Segment(1, 3)
        >>> s3 = Segment(2, 6)
        >>> s4 = Segment(1, 2)
        >>> for s in sorted([s1, s2, s3, s4]):
        ...    print s
        [1 --> 2]
        [1 --> 3]
        [1 --> 3]
        [2 --> 6]
    
    Start time difference
    
        >>> s1 = Segment(1, 3)
        >>> s2 = Segment(10, 23)
        >>> print s2 - s1
        9.0
    
    """
    
    def __init__(self, start=0., end=0.):
        super(Segment, self).__init__()
        self._start = float(start)
        self._end   = float(end)
    
    def _get_start(self): 
        return self._start
    def _set_start(self, value):
        self._start = value
    start = property(fget=_get_start, fset=_set_start, fdel=None)
    """Start time, in seconds.

    Examples
    --------

    >>> segment = Segment(start=13., end=37)
    >>> print segment.start
    13
    >>> segment.start = 36
    >>> print segment
    [36 --> 37]

    """
    
    def _get_end(self): 
        return self._end
    def _set_end(self, value):
        self._end = value
    end = property(fget=_get_end, fset=_set_end)
    """Get/set end time, in seconds.
    
    See Also
    --------
    pyannote.base.segment.Segment.start

    """
    
    def __nonzero__(self):
        """Use the expression 'if segment'
        
        Returns
        -------
        valid : bool
            False is segment is empty, True otherwise.
            
        """
        return self.end - self.start > SEGMENT_PRECISION
    
    
    def _get_duration(self):
        return self.end-self.start if self else 0.
    duration = property(fget=_get_duration)
    """Get segment duration, in seconds."""
    
    def _get_middle(self):
        return .5*(self.start+self.end)
    middle = property(fget=_get_middle)
    """Get segment middle time, in seconds."""
    
    def copy(self):
        """Duplicate segment."""
        return Segment(start=self.start, end=self.end)
    
    def __lt__(self, other):
        """Use the expression 'segment < other'"""
        return (self.start < other.start) or \
               ((self.start == other.start) and (self.end < other.end))
    
    def __le__(self, other):
        """Use the expression 'segment <= other'"""
        return (self.start < other.start) or \
               ((self.start == other.start) and (self.end <= other.end)) 
    
    def __eq__(self, other):
        """Use the expression 'segment == other'"""
        if isinstance(other, Segment):
            return (self.start == other.start) and \
                   (self.end == other.end)
        else:
            return False
        
    def __ne__(self, other):
        """Use the expression 'segment != other'"""
        return (self.start != other.start) or \
               (self.end != other.end)
    
    def __ge__(self, other):
        """Use the expression 'segment >= other'"""
        return other.__le__(self)
            
    def __gt__(self, other):
        """Use the expression 'segment > other'"""
        return other.__lt__(self)
    
    def __hash__(self):
        return hash(self.start)
        
    # ------------------------------------------------------- #
    # Inclusion (in), intersection (&), union (|) and gap (^) #
    # ------------------------------------------------------- #
    
    def __contains__(self, other):
        """Use the expression 'other in segment'
        
        Returns
        -------
        contains : bool
            True if other segment is fully included, False otherwise

        """
        return (self.start <= other.start) and \
               (self.end   >= other.end)
    
    def __and__(self, other):
        """Use the expression 'segment & other'
        
        Returns
        -------
        segment : Segment
            Intersection of the two segments
        
        """
        start = max(self.start, other.start)
        end   = min(self.end,   other.end)
        return Segment(start=start, end=end)
    
    def intersects(self, other):
        """Check whether two segments intersect each other
        
        Parameters
        ----------
        other : Segment
            Other segment
        
        Returns
        -------
        intersects : bool
            True if segments intersect, False otherwise
        """
        if not self or not other:
            return False
        
        return (self.start == other.start) or \
        (self.start < other.start and other.start < self.end) or \
        (other.start < self.start and self.start < other.end)
    
    def __or__(self, other):
        """Use the expression 'segment | other'
        
        Returns
        -------
        segment : Segment
            Shortest segment that contains both segments
        
        """
        # if segment is empty, union is the other one
        if not self:
            return other
        # if other one is empty, union is self
        if not other:
            return self
        
        # otherwise, do what's meant to be...
        start = min(self.start, other.start)
        end   = max(self.end,   other.end)
        return Segment(start=start, end=end)
    
    def __xor__(self, other):
        """Use the expression 'segment ^ other'
        
        Returns
        -------
        segment : Segment
            Gap between the two segments

        """        
        # if segment is empty, xor is not defined
        if (not self) or (not other):
            raise ValueError('')
            
        start =  min(self.end, other.end)
        end   =  max(self.start, other.start)
        return Segment(start=start, end=end)
    
    # == segment + float
    # shift the whole segment to the right
    # [ 0 --> 1 ] + 3 = [ 3 --> 4 ]
    def __add__(self, shift):
        """Use the expression 'segment + shift'
        
        Parameters
        ----------
        shift : float
            Temporal shift, in seconds.
        
        Returns
        -------
        segment : Segment
            Shifted segment with `shift` seconds.
        
        """
        
        if isinstance(shift, Segment):
            raise TypeError("unsupported operand type(s) for +:"
                            "'Segment' and 'Segment'")
        try:
            start = self.start + shift
            end = self.end + shift
        except TypeError, e:
            raise TypeError("unsupported operand type(s) for +:"
                            "'Segment' and '%s'" % type(shift).__name__)
                            
        return Segment(start=start, end=end)
                
    def __radd__(self, shift):
        """Use the expression 'shift + segment'
        
        See Also
        --------
        __add__
        
        """
        return self.__add__(shift)
    
    def __sub__(self, other):
        """Use the expression 'segment - other' or 'segment - shift'
        
        Parameters
        ----------
        other : float or Segment
            Temporal shift or other segment
            
        Returns
        -------
        segment : Segment
            if `other` is a float.
        delta : float
            start time difference if `other` is a Segment
        
        """
        if isinstance(other, Segment):
            return self.start - other.start
        else:
            return self.__add__(-other)
    
    def __rshift__(self, shift):
        """Use the expression 'segment >> shift'
        
        Parameters
        ----------
        shift : float
            Temporal shift, in seconds.
        
        Returns
        -------
        segment : Segment
            Segment with shifted end time by `shift` seconds.
        
        """
        
        if isinstance(shift, Segment):
            raise TypeError("unsupported operand type(s) for +:"
                            "'Segment' and 'Segment'")
        try:
            start = self.start
            end = self.end + shift
        except TypeError, e:
            raise TypeError("unsupported operand type(s) for >>:"
                            "'Segment' and '%s'" % type(shift).__name__)
                            
        return Segment(start=start, end=end)
        
    def __lshift__(self, shift):
        """Use the expression 'segment << shift'
        
        Equivalent to 'segment >> (-shift)'

        See Also
        --------
        __rshift__
        
        """
        return self.__rshift__(-shift)
    
    def __rrshift__(self, shift):
        """Use the expression 'shift >> segment'
        
        Parameters
        ----------
        shift : float
            Temporal shift, in seconds.
        
        Returns
        -------
        segment : Segment
            Segment with shifted start time by `shift` seconds.
        
        """
        if isinstance(shift, Segment):
            raise TypeError("unsupported operand type(s) for +:"
                            "'Segment' and 'Segment'")
        try:
            start = self.start + shift
            end = self.end
        except TypeError, e:
            raise TypeError("unsupported operand type(s) for >>:"
                            "'Segment' and '%s'" % type(shift).__name__)
                            
        return Segment(start=start, end=end)
        
    def __rlshift__(self, shift):
        """Use the expression 'shift << segment'
        
        Equivalent to '(-shift) >> segment'

        See Also
        --------
        __rrshift__
        
        """        
        return self.__rrshift__(-shift)
    
    def __str__(self):
        """Use the expression str(segment)"""
        if self:
            return '[%g --> %g]' % (self.start, self.end)
        else:
            return '∅'
    
    def __repr__(self):
        
        return '<Segment(%g, %g)>' % (self.start, self.end)
    

class RevSegment(Segment):
    """Reversed segment.
    """
    
    def __init__(self, segment):
        super(RevSegment, self).__init__(start=segment.start, end=segment.end)    
    def __lt__(self, other):
        return (self.end < other.end) or \
               ((self.end == other.end) and (self.start > other.start))
    
    def __le__(self, other):
        return (self.end < other.end) or \
               ((self.end == other.end) and (self.start >= other.start)) 
    
    def __gt__(self, other):
        return other.__lt__(self)
        
    def __ge__(self, other):
        return other.__le__(self)
    
    def __eq__(self, other):
        return (self.start == other.start) and \
               (self.end == other.end)
        
    def __ne__(self, other):
        return (self.start != other.start) or \
               (self.end != other.end)
    
    def __sub__(self, other):
        if isinstance(other, RevSegment):
            return self.end - other.end
        return self.__add__(-other)
    
    def __str__(self):
        if self:
            return '[%g --> %g]' % (self.start, self.end)
        else:
            return '∅'
    
    def __repr__(self):
        return '<%s.RevSegment(%g, %g)>' % (__name__, self.start, self.end)

import numpy as np
class SlidingWindow(object):
    """Sliding window
    
    Parameters
    ----------
    duration : float > 0, optional
        Window duration, in seconds. Default is 30 ms.
    step : float > 0, optional
        Step between two consecutive position, in seconds. Default is 10 ms.
    start : float, optional
        First start position of window, in seconds. Default is 0.
    end : float > `start`, optional
        Default is infinity (ie. window keeps sliding forever)
    end_mode : {'strict', 'loose', 'intersection'}, optional
        Has no effect when `end` is infinity.
    
    Examples
    --------
    
    >>> sw = SlidingWindow(duration, step, start)    
    >>> frame_range = (a, b)
    >>> frame_range == sw.toFrameRange(sw.toSegment(*frame_range))
    ... True
    
    >>> segment = Segment(A, B)
    >>> new_segment = sw.toSegment(*sw.toFrameRange(segment))
    >>> abs(segment) - abs(segment & new_segment) < .5 * sw.step
    
    """
    def __init__(self, duration=0.030, step=0.010, \
                       start=0.000, end=None, end_mode='intersection'):
        super(SlidingWindow, self).__init__()
        
        # duration must be a float > 0
        if duration <= 0:
            raise ValueError("'duration' must be a float > 0.")
        self.__duration = duration

        # step must be a float > 0
        if step <= 0:
            raise ValueError("'step' must be a float > 0.")
        self.__step = step

        # start must be a float.
        self.__start = start

        # if end is not provided, set it to infinity
        if end is None:
            self.__end = np.inf
        else:
            # end must be greater than start
            if end <= start:
                raise ValueError("'end' must be greater than 'start'.")
            self.__end = end
        
        # allowed end modes are 'intersection', 'strict' or 'loose'
        if not end_mode in ['intersection', 'strict', 'loose']:
            raise ValueError("unsupported 'end_mode'.")
        self.__end_mode = end_mode
    
    
    def __get_start(self): 
        return self.__start
    start = property(fget=__get_start)
    """Sliding window start time in seconds."""
    
    def __get_end(self): 
        return self.__end
    end = property(fget=__get_end)
    """Sliding window end time in seconds."""
    
    def __get_end_mode(self): 
        return self.__end_mode
    end_mode = property(fget=__get_end_mode)
    """Sliding window end mode."""

    def __get_step(self): 
        return self.__step
    step = property(fget=__get_step)
    """Sliding window step in seconds."""
    
    def __get_duration(self): 
        return self.__duration
    duration = property(fget=__get_duration)
    """Sliding window duration in seconds."""
    
    def __closest_frame(self, t):
        """Closest frame to timestamp.
        
        Parameters
        ----------
        t : float
            Timestamp, in seconds.
            
        Returns
        -------
        index : int
            Index of frame whose middle is the closest to `timestamp`
        
        """
        frame = np.rint(.5+(t-self.__start-.5*self.__duration)/self.__step)
        return int(frame)
    
    def segmentToRange(self, segment):
        """Convert segment to 0-indexed frame range
        
        Parameters
        ----------
        segment : Segment
        
        Returns
        -------
        i0 : int
            Index of first frame
        n : int
            Number of frames
        
        Examples
        --------
        
            >>> window = SlidingWindow()
            >>> print window.segmentToRange(Segment(10, 15))
            i0, n
        
        """
        # find closest frame to segment start
        i0 = self.__closest_frame(segment.start)
        # find closest frame to segment end
        j0 = self.__closest_frame(segment.end)
        # return frame range as (start_frame, number_of_frame) tuple
        i0 = max(0, i0)
        n = j0 - i0
        return i0, n
    
    def rangeToSegment(self, i0, n):
        """Convert 0-indexed frame range to segment
        
        Each frame represents a unique segment of duration 'step', centered on
        the middle of the frame. 
        
        The very first frame (i0 = 0) is the exception. It is extended to the
        sliding window start time.

        Parameters
        ----------
        i0 : int
            Index of first frame
        n : int 
            Number of frames
            
        Returns
        -------
        segment : Segment
        
        Examples
        --------
        
            >>> window = SlidingWindow()
            >>> print window.rangeToSegment(3, 2)
            [ --> ]
        
        """
        
        # frame start time
        # start = self.start + i0 * self.step
        # frame middle time
        # start += .5 * self.duration
        # subframe start time
        # start -= .5 * self.step
        start = self.__start + (i0-.5)*self.__step + .5*self.__duration
        duration = n*self.__step
        segment = Segment(start, start + duration)
        
        if i0 == 0:
            # extend segment to the beginning of the timeline
            segment.start = self.start
        
        return segment
        
    def __getitem__(self, i):
        """
        Parameters
        ----------
        i : int
            Index of sliding window position
            
        Returns
        -------
        segment : :class:`Segment`
            Sliding window at ith position.
        
        """
        
        # window start time at ith position
        start = self.__start + i*self.__step
        
        # in case segment starts after the end,
        # return an empty segment 
        if start >= self.__end:
            return Segment(start, start)
        
        # window end time at ith position
        end = start + self.__duration
        
        # in case segment ends after the end,
        if end > self.__end:
            
            # return a trimmed segment in 'intersection' mode
            if self.__end_mode == 'intersection':
                end = self.__end 

            # return an empty segment in 'strict' mode
            elif self.__end_mode == 'strict': 
                start = end
            
            # return the full segment in 'loose' mode
            # elif self.__end_mode == 'loose':
            #     pass
        
        return Segment(start, end)
        
    def __iter__(self):
        """Sliding window iterator
        
        Use expression 'for segment in sliding_window'
        
        Examples
        --------
        
            >>> window = SlidingWindow(end=0.1)
            >>> for segment in window:
            ...     print segment
            [0 --> 0.03]
            [0.01 --> 0.04]
            [0.02 --> 0.05]
            [0.03 --> 0.06]
            [0.04 --> 0.07]
            [0.05 --> 0.08]
            [0.06 --> 0.09]
            [0.07 --> 0.1]
            [0.08 --> 0.1]
            [0.09 --> 0.1]
        
        """
        
        # get window first position
        i = 0
        window = self[i]
        
        # yield window while it's valid 
        while(window):
            yield window
            
            # get window next position
            i += 1
            window = self[i]
    
    def __len__(self):
        """Number of positions
        
        Equivalent to len([segment for segment in window])
        
        Returns
        -------
        length : int
            Number of positions taken by the sliding window
            (from start times to end times)
        
        """
        if np.isinf(self.__end):
            raise ValueError('infinite sliding window.')
        
        # start looking for last position 
        # based on frame closest to the end
        i = self.__closest_frame(self.__end)
        
        # in 'strict' mode, look into previous frames
        if self.__end_mode == 'strict':
            while(not self[i]):
                i -= 1
            length = i+1
        
        # in 'loose' or 'intersection' mode, look into next frames
        else:
            while(self[i]):
                i += 1
            length = i
        
        return length
    
    
    def copy(self):
        """Duplicate sliding window"""
        duration = self.duration
        step = self.step
        start = self.start
        end = self.end
        end_mode = self.end_mode
        sliding_window = SlidingWindow(duration=duration, step=step,
                                       start=start, end=end, 
                                       end_mode=end_mode)
        return sliding_window
        
if __name__ == "__main__":
    import doctest
    doctest.testmod()
