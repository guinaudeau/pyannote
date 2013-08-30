#!/usr/bin/env python
# encoding: utf-8

# Copyright 2012-2013 Herve BREDIN (bredin@limsi.fr)

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
from collections import namedtuple

SEGMENT_PRECISION = 1e-6


class Segment(namedtuple('Segment', ['start', 'end'])):
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
    start, end : float
        `start` and `end` times, in seconds.

    Returns
    -------
    segment : Segment
        New segment with `start` and `end` times.

    Examples
    --------
    Create a new temporal interval between 00:13.000 and 00:37.000.

        >>> segment = Segment(start=13., end=37)
        >>> print segment
        [13.000 --> 37.000]

    Inclusion, intersection, union & gap

        >>> s1 = Segment(1, 2)
        >>> s2 = Segment(0, 3)
        >>> if s1 in s2:
        ...    print "Segment %s is included in segment %s." % (s1, s2)
        Segment [1.000 --> 2.000] is included in segment [0.000 --> 3.000].
        >>> s3 = Segment(2, 5)
        >>> print s1 & s3
        ∅
        >>> print s2 & s3
        [2.000 --> 3.000]
        >>> print s2 | s3
        [0.000 --> 5.000]
        >>> print s1 ^ Segment(5, 7)
        [2.000 --> 5.000]

    Test whether segment is empty or not.

        >>> if not Segment(10, 10):
        ...    print "Segment is empty."
        Segment is empty.

    Comparison

        >>> s1 = Segment(1, 3)
        >>> s2 = Segment(1, 3)
        >>> s3 = Segment(2, 6)
        >>> s4 = Segment(1, 2)
        >>> for s in sorted([s1, s2, s3, s4]):
        ...    print s
        [1.000 --> 2.000]
        [1.000 --> 3.000]
        [1.000 --> 3.000]
        [2.000 --> 6.000]

    """

    def __new__(cls, start=0., end=0.):
        # add default values
        return super(Segment, cls).__new__(cls, start, end)

    def __nonzero__(self):
        """Use the expression 'if segment'

        Returns
        -------
        valid : bool
            False is segment is empty, True otherwise.

        """
        return bool((self.end - self.start) > SEGMENT_PRECISION)

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
        return (self.start <= other.start) and (self.end >= other.end)

    def __and__(self, other):
        """Use the expression 'segment & other'

        Returns
        -------
        segment : Segment
            Intersection of the two segments

        """
        start = max(self.start, other.start)
        end = min(self.end, other.end)
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
               (self.start < other.start and other.start < self.end-SEGMENT_PRECISION) or \
               (self.start > other.start and self.start < other.end-SEGMENT_PRECISION)

    def overlaps(self, t):
        return self.start <= t and self.end >= t

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
        end = max(self.end, other.end)
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

        start = min(self.end, other.end)
        end = max(self.start, other.start)
        return Segment(start=start, end=end)

    def __str__(self):
        """Use the expression str(segment)"""
        if self:
            return '[%.3f --> %.3f]' % (self.start, self.end)
        else:
            return '∅'

    def _pretty(self, seconds):
        from datetime import timedelta
        td = timedelta(seconds=seconds)
        days = td.days
        seconds = td.seconds
        microseconds = td.microseconds
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if abs(days) > 0:
            return '%d:%02d:%02d:%02d.%03d' % (days, hours, minutes,
                                               seconds, microseconds/1000)
        else:
            return '%02d:%02d:%02d.%03d' % (hours, minutes, seconds,
                                            microseconds/1000)

    def pretty(self):
        """Human-readable representation of segments"""
        return '[%s --> %s]' % (self._pretty(self.start),
                                self._pretty(self.end))

    def __repr__(self):
        return '<Segment(%g, %g)>' % (self.start, self.end)

    def to_json(self):
        return {'start': self.start, 'end': self.end}


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

    def __init__(self, duration=0.030, step=0.010, start=0.000, end=None):
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

    def __get_start(self):
        return self.__start
    start = property(fget=__get_start)
    """Sliding window start time in seconds."""

    def __get_end(self):
        return self.__end
    end = property(fget=__get_end)
    """Sliding window end time in seconds."""

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
        return int(np.rint((t-self.__start-.5*self.__duration)/self.__step))

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
            Sliding window at ith position

        """

        # window start time at ith position
        start = self.__start + i*self.__step

        # in case segment starts after the end,
        # return an empty segment
        if start >= self.__end:
            return None

        return Segment(start=start, end=start+self.__duration)

    def __iter__(self):
        """Sliding window iterator

        Use expression 'for segment in sliding_window'

        Examples
        --------

            >>> window = SlidingWindow(end=0.1)
            >>> for segment in window:
            ...     print segment
            [0.000 --> 0.030]
            [0.010 --> 0.040]
            [0.020 --> 0.050]
            [0.030 --> 0.060]
            [0.040 --> 0.070]
            [0.050 --> 0.080]
            [0.060 --> 0.090]
            [0.070 --> 0.100]
            [0.080 --> 0.100]
            [0.090 --> 0.100]

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
        sliding_window = SlidingWindow(
            duration=duration, step=step, start=start, end=end
        )
        return sliding_window


class YaafeFrame(SlidingWindow):
    """Yaafe frames

    Parameters
    ----------
    blockSize : int, optional
        Window size (in number of samples). Default is 512.
    stepSize : int, optional
        Step size (in number of samples). Default is 256.
    sampleRate : int, optional
        Sample rate (number of samples per second). Default is 16000.

    References
    ----------
    http://yaafe.sourceforge.net/manual/quickstart.html

    """
    def __init__(self, blockSize=512, stepSize=256, sampleRate=16000):

        duration = 1. * blockSize / sampleRate
        step = 1. * stepSize / sampleRate
        start = -0.5 * duration

        super(YaafeFrame, self).__init__(
            duration=duration, step=step, start=start
        )


if __name__ == "__main__":
    import doctest
    doctest.testmod()
