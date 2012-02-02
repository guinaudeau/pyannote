.. currentmodule:: pyannote

=======
Segment
=======

A segment is uniquely defined by its start and end times (in seconds)::

    >>> from pyannote import Segment
    >>> segment = Segment(start=13., end=37)
    >>> print segment
    [13 --> 37]

**start** and **end** attributes can be used directly to read or modify a segment::

	>>> print segment.start
	13.0
	>>> segment.end = 14.
	>>> print segment
	[13 --> 14]

The duration (in seconds) of a segment can be obtained via the **abs()** operator::

    >>> print abs(segment)
    1.0

Read-only **middle** attribute can be used to get the segment middle time::

    >>> print segment.middle
    13.5

A segment is empty in case start time is greater than (or equals) end time.
One can check if a segment is **empty** using the following::

    >>> if segment:
            print "Segment is not empty."
        else:
            print "Segment is empty."
	Segment is not empty. 

   
Comparison
----------

Two segments can be compared for equality as expected::

   >>> segment1 = Segment(1, 2)
   >>> segment2 = Segment(1, 2)   
   >>> if segment1 == segment2:
           print "Segments are identical"

Other **comparison** operators <, >, <= and >= are also available.
Segment A is smaller than segment B if (and only if)

* A starts before B
* or A and B starts simultaneously and A ends before B.

   >>> Segment(0, 1) < Segment(3, 4)
   True

Inclusion of one segment into another can be tested with the **in** operator::

   >>> big_segment = Segment(10, 20)
   >>> small_segment = Segment(12, 13)
   >>> if small_segment in big_segment:
          print "Small segment is fully included in big segment."
   Small segment is fully included in big segment.
   
**Intersection** of two segments is obtained with the **&** operator::
   
   >>> segment1 = Segment(3, 5)
   >>> segment2 = Segment(4, 6)
   >>> print segment1 & segment2
   [4 --> 5]
   
**Union** (operator |) of two segments returns the minimum-duration segment that contains both of them::
   
   >>> print segment1 | segment2
   [3 --> 6]
   
Operator ^ returns the gap between two segments::
   
   >>> print segment1 ^ segment2
   ∅
   >>> print Segment(0, 10) ^ (15, 25)
   [10 --> 15]

Other operations
----------------

Segments can be modified in many ways. Here are a few examples:

* Shift the whole segment by 4 seconds in the future::

   >>> segment = Segment(13, 14)
   >>> segment += 4.
   >>> print segment
   [17 --> 18]
   
* Make segment last longer by 8 seconds::
    
   >>> new_segment = segment >> 8
   >>> print new_segment
   [17 --> 26]

* Shorten segment by 0.1 second on each side::

   >>> new_segment = .1 >> segment << .1
   >>> print new_segment
   [17.1 --> 17.9]

    

