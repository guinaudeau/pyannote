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
    start

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


if __name__ == "__main__":
    import doctest
    doctest.testmod()
