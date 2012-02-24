.. currentmodule:: pyannote

========
Timeline
========

Create empty timeline for video 'MyMovie.avi'::

	>>> from pyannote import *
	>>> timeline = Timeline(video='MyMovie.avi')

Get/update video attribute::

   >>> video = timeline.video
   >>> timeline.video = 'video.mpg'
   
A timeline is said to be empty in case it contains no segment::

    >>> if not timeline:
    ...     print 'Timeline is empty.'
    Timeline is empty.

Add three segments to timeline::

    >>> timeline += Segment(0, 1)
    >>> timeline += Segment(2, 4)
    >>> timeline += Segment(3, 5)

One can get the number of segments using **len()**::

    >>> print 'Timeline has %d segments.' % len(timeline)
    Timeline has 3 segments.

A segment **cannot** be added twice to a timeline. If it already exists, it is simply not added a second time::

    >>> timeline += Segment(2, 4)
    >>> print 'Timeline still has %d segments.' % len(timeline)
    Timeline still has 3 segments.
    >>> print timeline
    [
       [0 --> 1]
       [2 --> 4]
       [3 --> 5]
    ]

One can add all segments of another timeline at once:: 

    >>> other_segments = [Segment(6,7), Segment(8, 9)]
    >>> other_timeline = Timeline(segments=other_segments, video='video.mpg')
    >>> timeline += other_timeline
    >>> print timeline
    [
       [0 --> 1]
       [2 --> 4]
       [3 --> 5]
       [6 --> 7]
       [8 --> 9]
    ]

In case something had to be done for each segment in timeline, it is possible to iterate through all segments in timeline, in chronological order (i.e. sorted with < comparison operator)::

	>>> for s, segment in enumerate(timeline):
	...     print 'Segment %d is %s' % (s+1, segment)
	Segment 1 is [0 --> 1]
	Segment 2 is [2 --> 4]
	Segment 3 is [3 --> 5]
	Segment 4 is [6 --> 7]
	Segment 5 is [8 --> 9]


Segments can be accessed either individually or as slices.

* Get 3rd segment::

   >>> third_segment = timeline[2]
   >>> print third_segment
   [3 --> 5]
    
* Get segments 3, 4 and 5 in a list::

   >>> segments = timeline[3:6]

Combined with **in** operator, **index()** method can be used to retrieve the position of a segment in a timeline::

    >>> look_for = Segment(3, 5)
    >>> if look_for in timeline:
    ...     i = timeline.index(look_for)
    ...     print 'Segment %s is at index %d.' % (look_for, i)
    Segment [3 --> 5] is at index 2.
            
:note: 

    index() raises an error if timeline does not contain requested segment::

        >>> timeline.index(Segment(2, 3))
        Traceback (most recent call last):
          ...
        ValueError: segment [2 --> 3] is not in timeline


The extent of a timeline is defined as the segment of minimum duration that contains the whole timeline::

  >>> extent = timeline.extent()
  >>> print extent
  [0 --> 9]

The coverage of a timeline is defined as the timeline of minimum length (ie. minimum number of segments) that covers exactly the same time ranges as the original timeline::

   >>> coverage = timeline.coverage()
   >>> print coverage
   [
      [0 --> 1]
      [2 --> 5]
      [6 --> 7]
      [8 --> 9]
   ]
    
The duration of a timeline is defined as the sum of the duration of all segments in timeline coverage::

   >>> duration = timeline.duration()
   >>> print 'Timeline has a duration of %g seconds.' % duration
   Timeline has a duration of 6 seconds.
   
Get duplicate timeline::

   >>> duplicate = timeline.copy()

Sub-timelines
-------------

Timeline objects are *callable* and this property can be used to get sub-timelines in multiple ways (depending on the **mode** parameter)

* Sub-timeline made of segments fully included in requested segment (**strict** mode)::
   
    >>> requested_segment = Segment(2.5, 6.5)
    >>> sub_timeline = timeline(requested_segment, mode='strict')
    >>> print sub_timeline
    [
       [3 --> 5]
    ]
   
* Sub-timeline made of segments with non-emtpy intersection with requested segment (**loose** mode)::
   
    >>> sub_timeline = timeline(requested_segment, mode='loose')
    >>> print sub_timeline
    [
       [2 --> 4]
       [3 --> 5]
       [6 --> 7]
    ]
    
* **intersection** mode -- same as **loose** mode, except segments that are not fully included in requested segment are trimmed to be fully included::
   
    >>> sub_timeline = timeline(requested_segment, mode='intersection')
    >>> print sub_timeline
    [
       [2.5 --> 4]
       [3 --> 5]
       [6 --> 6.5]
    ]
    
Sub-timeline based on another timeline can also be computed.

* Sub-timeline made of segments fully included in requested timeline coverage::
   
   >>> requested_timeline = Timeline(video='MyVideo.avi')
   >>> requested_timeline += Segment(0.5, 2)
   >>> requested_timeline += Segment(8, 10)
   >>> sub_timeline = timeline(requested_timeline, mode='strict')
   >>> print sub_timeline
   [
      [8 --> 9]
   ]

* Sub-timeline made of segments with non-empty intersection with requested timeline coverage::

   >>> sub_timeline = timeline(requested_timeline, mode='loose')
   >>> print sub_timeline
   [
      [0 --> 1]
      [8 --> 9]
   ]
    
* **intersection** mode -- same as **loose**, except segments that are not fully included in requested timeline coverage are trimmed to be fully included::
   
   >>> sub_timeline = timeline(requested_timeline, mode='intersection')
   >>> print sub_timeline
   [
      [0.5 --> 1]
      [8 --> 9]
   ]
    
Partitions and gaps
-------------------

A timeline is a partition if it contains no overlapping segments.

Using the **abs()** operator, one can create a partition from a timeline with the same set of segment boundaries and the same coverage::

    >>> timeline = Timeline(video='MyVideo.avi')
    >>> timeline += Segment(1, 3)
    >>> timeline += Segment(2, 4)
    >>> timeline += Segment(5, 6)
    >>> partition = abs(timeline)
    >>> print partition
    [
       [1 --> 2]
       [2 --> 3]
       [3 --> 4]
       [5 --> 6]
    ]

Check whether timeline is a partition::

    >>> if timeline > 0:
    ...     print "Timeline is a partition."
    ... else: 
    ...     print "Timeline is not a partition." 
    Timeline is not a partition.
    
A timeline might contains gaps (or holes) in its coverage.
Use inversion (~) operator to get them::

    >>> gaps = ~timeline # or gaps = 1 / timeline
    >>> print gaps
    [
       [4 --> 5]
    ]
    
More generally, it is possible to get the minimum length timeline necessary to fill timeline (at least) up to a provided coverage::

   >>> requested_coverage = Segment(0, 30)
   >>> gaps = requested_coverage / timeline
   >>> print gaps
   [
      [0 --> 1]
      [4 --> 5]
      [6 --> 30]
   ]
   >>> print (timeline + gaps).coverage()
   [
      [0 --> 30]
   ]
    
   >>> requested_coverage = Timeline(video='MyVideo.avi')
   >>> requested_coverage += Segment(0, 5)
   >>> requested_coverage += Segment(10, 30)
   >>> gaps = requested_coverage / timeline
   >>> print gaps
   [
      [0 --> 1]
      [4 --> 5]
      [10 --> 30]
   ]
   >>> print (gaps+timeline).coverage()
   [
      [0 --> 6]
      [10 --> 30]
   ]
   

