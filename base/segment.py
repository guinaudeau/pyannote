#!/usr/bin/env python
# encoding: utf-8

SEGMENT_PRECISION = 1e-6

class Segment(object):
    """
A segment is uniquely defined by its start and end times (in seconds)::

    >>> from pyannote import Segment
    >>> segment = Segment(start=13., end=37)
    >>> print segment
    [13 --> 37]

    """
    
    def __init__(self, start=0., end=0.):
        """
        Initialize a segment with start and end time.
        
        Parameters
        ----------
        start : float
            Start time in seconds
        end : float
            End time in seconds
        """
        super(Segment, self).__init__()
        self._start = float(start)
        self._end   = float(end)
    
    # --------------- #
    # Getters/Setters #
    # --------------- #
    
    def _get_start(self): 
        return self._start
    def _set_start(self, value):
        self._start = value
    start = property(fget=_get_start, fset=_set_start, fdel=None, doc="Segment start time (in seconds).")
    # begin = property(fget=_get_start, fset=_set_start, fdel=None, doc="Segment start time in seconds.")
    # left  = property(fget=_get_start, fset=_set_start, fdel=None, doc="Segment start time in seconds.")
    
    def _get_end(self): 
        return self._end
    def _set_end(self, value):
        self._end = value
    end   = property(fget=_get_end, fset=_set_end, fdel=None, doc="Segment end time (in seconds).")
    # stop  = property(fget=_get_end, fset=_set_end, fdel=None, doc="Segment end time in seconds.")
    # right = property(fget=_get_end, fset=_set_end, fdel=None, doc="Segment end time in seconds.")
    
    def __nonzero__(self):
        """
        Return True if segment is not empty, False otherwise.
        Use the expression 'if segment'
        
        Examples
        --------
        
        >>> segment = qc.Segment()
        >>> if not segment:
                print 'Segment is empty.'
        Segment is empty.
        >>> segment.end = 5
        >>> if segment:
                print 'Segment duration is %g seconds.' % (abs(segment))
        Segment duration 5 seconds.        
        """
        return self.end - self.start > SEGMENT_PRECISION
    
    def __abs__(self):
        """
        Return duration of segment, in seconds.
        
        Returns
        -------
        duration: float
                  The duration of the segment, in seconds.
        """
        if self:
            return self.end - self.start
        else:
            return 0.
    
    def _get_duration(self):
        return abs(self)
    duration = property(fget=_get_duration, fset=None, fdel=None, doc="Segment duration in seconds.")
    
    def _get_middle(self):
        return .5*(self.start+self.end)
    middle = property(fget=_get_middle, fset=None, fdel=None, doc="Segment mid time in seconds.")
    center = property(fget=_get_middle, fset=None, fdel=None, doc="Segment mid time in seconds.")
    
    def copy(self):
        """
        Return a copy of the segment
        
        Returns
        -------
        segment : Segment
                  A copy of the segment
        """
        return Segment(start=self.start, end=self.end)
    
    # -------------------------------------------- #
    # Comparison operators (<, <=, ==, !=, >=, >)  #
    # -------------------------------------------- #
    def __lt__(self, other):
        return (self.start < other.start) or \
               ((self.start == other.start) and (self.end < other.end))
    
    def __le__(self, other):
        return (self.start < other.start) or \
               ((self.start == other.start) and (self.end <= other.end)) 
    
    def __eq__(self, other):
        if isinstance(other, Segment):
            return (self.start == other.start) and \
                   (self.end == other.end)
        else:
            return False
        
    def __ne__(self, other):
        return (self.start != other.start) or \
               (self.end != other.end)
    
    def __ge__(self, other):
        return other.__le__(self)
            
    def __gt__(self, other):
        return other.__lt__(self)
    
    def __hash__(self):
        return hash(self.start)
        
    # ------------------------------------------------------- #
    # Inclusion (in), intersection (&), union (|) and gap (^) #
    # ------------------------------------------------------- #
    
    def __contains__(self, other):
        """
        Return True if other segment is fully included in the segment,
        False otherwise. Use the expression 'other_segment in segment'.
        
        Examples
        --------
        
        >>>
        >>>
        True
        >>>
        False
        
        """
        return (self.start <= other.start) and \
               (self.end   >= other.end)
    
    def __and__(self, other):
        """
        Return intersection of segments
        Use expression 'segment1 & segment2'
        """
        start = max(self.start, other.start)
        end   = min(self.end,   other.end)
        return Segment(start=start, end=end)
    
    def __or__(self, other):
        """
        Return shortest segment containing both segments
        Use expression 'segment1 | segment2'
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
        """
        Return gap between segments
        Use expression 'segment1 ^ segment2'
        """
        
        # if segment is empty, xor is not defined
        if (not self) or (not other):
            raise ValueError('')
            
        start =  min(self.end, other.end)
        end   =  max(self.start, other.start)
        return Segment(start=start, end=end)
    
    # --------------------- #
    # Arithmetic operations #
    # --------------------- #
    
    # == segment + float
    # shift the whole segment to the right
    # [ 0 --> 1 ] + 3 = [ 3 --> 4 ]
    def __add__(self, other):
        if isinstance(other, Segment):
            raise TypeError("unsupported operand type(s) for -: 'Segment' and 'Segment'")
        start = self.start + other
        end   = self.end   + other
        return Segment(start=start, end=end)
    
    # == float + segment
    # shift the whole segment to the right
    # 3 + [ 0 --> 1 ] = [ 3 --> 4 ]
    def __radd__(self, other):
        return self.__add__(other)
    
    # == segment - float
    # shift the whole segment to the left
    # [ 0 --> 1 ] - 3 = [ -3 --> -2 ]
    # == segment - segment
    # difference in start time
    def __sub__(self, other):
        if isinstance(other, Segment):
            return self.start - other.start
        return self.__add__(-other)
    
    # == segment >> float
    # increase segment duration from the right
    # [ 0 --> 1 ] >> 3 = [ 0 --> 4 ]
    def __rshift__(self, other):
        if isinstance(other, Segment):
            raise TypeError("unsupported operand type(s) for >>: 'Segment' and 'Segment'")
        start = self.start
        end   = self.end + other
        return Segment(start=start, end=end)
    
    # == segment << float
    # reduce segment duration from the right
    # [ 0 --> 1 ] << 3 = [ 0 --> -2 ]
    def __lshift__(self, other):
        return self.__rshift__(-other)
    
    # == float << segment
    # increase segment duration from the left
    # 3 >> [ 0 --> 1 ] = [ 3 --> 1 ]
    def __rrshift__(self, other):
        if isinstance(other, Segment):
            raise TypeError("unsupported operand type(s) for >>: 'Segment' and 'Segment'")
        start = self.start + other
        end   = self.end
        return Segment(start=start, end=end)
    
    # == float >> segment
    # reduce segment duration from the left
    # 3 << [ 0 --> 1 ] = [ -3 --> 1 ]
    def __rlshift__(self, other):
        return self.__rrshift__(-other)
    
    # --------------------- #
    # String representation #
    # --------------------- #
    
    def __str__(self):
        if self:
            return '[%g --> %g]' % (self.start, self.end)
        else:
            return '∅'
    
    def __repr__(self):
        return '<%s.Segment(%g, %g)>' % (__name__, self.start, self.end)
    

class RevSegment(Segment):
    
    def __init__(self, segment):
        super(RevSegment, self).__init__(start=segment.start, end=segment.end)    
    
    # -------------------------------------------- #
    # Comparison operators (<, <=, ==, !=, >=, >)  #
    # -------------------------------------------- #
    
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
    