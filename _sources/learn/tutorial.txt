.. This file is part of PyAnnote

      PyAnnote is free software: you can redistribute it and/or modify
      it under the terms of the GNU General Public License as published by
      the Free Software Foundation, either version 3 of the License, or
      (at your option) any later version.
  
      PyAnnote is distributed in the hope that it will be useful,
      but WITHOUT ANY WARRANTY; without even the implied warranty of
      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
      GNU General Public License for more details.
  
      You should have received a copy of the GNU General Public License
      along with PyAnnote.  If not, see <http://www.gnu.org/licenses/>.

Tutorial
========

This tutorial will walk you through the main concepts of ``PyAnnote`` in a 
matter of minutes. Let's get started::

	>>> from pyannote import Segment, Timeline, Annotation
	
The main ``PyAnnote`` objects are segments, timelines and annotations. 

Segments
********

Segments are meant to store temporal intervals. 

	>>> start_time_in_seconds = 10
	>>> end_time_in_seconds = 20
	>>> segment = Segment(start=start_time_in_seconds, end=end_time_in_seconds)
	>>> print "Segment %s starts at %g seconds and ends at %g seconds." % \
	... (segment, segment.start, segment.stop)
	Segment [10 --> 20] starts at 10 seconds and ends at 20 seconds.	

Intersection of two segments is obtained via the operator &.
	
	>>> other_segment = Segment(15, 25)
	>>> if segment & other_segment:
	...      print "Intersection of %s and %s is %s." % \
	...      (segment, other_segment, segment & other_segment)
	Intersection of [10 --> 20] and [15 --> 25] is [15 --> 20].

A segment can be reduced or extended using operators >> and <<.

	>>> print segment << 3
	[10 --> 17]
	>>> print 3 << segment
	[7 --> 20]
	>>> print 1 >> segment << 2
	[11 --> 18]
	
This is only a very short description of what you can do with segments. 
There are **many** more possibilities. Use ``>>> help(Segment)`` for a complete description.

Timelines
*********

A timeline can be seen as a set of ordered segments, describing a given (audio or video) document, whose name is provided with the ``video`` parameter.

	 >>> timeline = Timeline(video='MyVideo.avi')
	 >>> for start_time in range(0, 5):
	 ...     timeline += Segment(start_time, start_time + 2)
	 >>> print "Timeline contains %d (possibly overlapping) segments." % \
	 ...                                                     len(timeline)
	 Timeline contains 5 (possibly overlapping) segments.
	 >>> print timeline
	 [
	    [0 --> 2]
	    [1 --> 3]
	    [2 --> 4]
	    [3 --> 5]
	    [4 --> 6]
	 ]
	 
Getting or deleting a segment is easy as well.

	>>> print "Third segment is %s." % timeline[2]
	Third segment is [2 --> 4].
	>>> del timeline[2:4]
	>>> for segment in timeline:
	...    print segment
	[0 --> 2]
	[1 --> 3]
	[4 --> 6]

``PyAnnote`` also allows to compute a timeline extent, coverage, duration or 
gaps. See ``>>> help(Timeline)`` for their detailed definition.

	>>> print "The extent is segment %s." % timeline.extent()
	The extent is segment [0 --> 6].
	>>> print "The coverage is:\n%s" % timeline.coverage()
	The coverage is:
	[
	   [0 --> 3]
	   [4 --> 6]
	]
	>>> print "It covers %g seconds." % timeline.duration()
	It covers 5 seconds.
	>>> print "It contains the following gaps:\n%s" % timeline.gaps()
	It contains the following gaps:
	[
	   [3 --> 4]
	]

Finally, one can extract a subset of a timeline.

	>>> segment = Segment(2, 5)
	>>> print timeline(segment)
	[
	   [1 --> 3]
	   [4 --> 5]
	]
	
In *loose* mode, any intersecting segments are kept unmodified.
	
	>>> print timeline(segment, mode='loose')
	[
	   [1 --> 3]
	   [4 --> 6]
	]

In *strict* mode, only fully included segments are kept.
	
	>>> print timeline(segment, mode='strict')
	[
	   [1 --> 3]
	]


This is only a very short description of what you can do with segments.
There are **many** more possibilites. Use ``>>> help(Timeline)`` for a complete description.

Annotations
***********

Annotations are probably the objects you will manipulate the most when using
``PyAnnote``. 

For instance, let us create an annotation meant to store the output of a speaker
identification algorithms for video *MyVideo.avi*. 
We can easily do so using the following commands:

	>>> speaker = Annotation(multitrack=False, \
	...                      video='MyVideo.avi', modality='speaker')
	>>> speaker[Segment(0, 10)] = 'Alice'
	>>> speaker[Segment(10, 15)] = 'Bob'
	>>> speaker[Segment(14, 20)] = 'Alice'
	>>> speaker[Segment(23, 30)] = 'Bob'
	>>> for segment, label in speaker.iterlabels():
	...    print "%s speaks during %s." % (label, segment)
	Alice speaks during [0 --> 10].
	Bob speaks during [10 --> 15].
	Alice speaks during [14 --> 20].
	Bob speaks during [10 --> 15].

If we want to focus on Alice's speech turns, we can just extract the corresponding annotation subset (same for Bob):

	>>> alice = speaker('Alice')
	>>> print alice
	[
	   [0 --> 10] : Alice
	   [14 --> 20] : Alice
	]
	>>> bob = speaker('Bob')

Obviously, we can obtain some kind of statistics about speakers:

	>>> print "Alice spoke for %g seconds." % alice.timeline.duration()
	Alice spoke for 16 seconds.
	>>> print "Alice and Bob spoke simultaneously at:\n%s" % \
	...                           (alice.timeline & bob.timeline)
	Alice and Bob spoke simultaneously at:
	[
	   [14 --> 15]
	]

This is only a very short description of what you can do with segments.
There are **many** more possibilites. Use ``>>> help(Annotation)`` for a
complete description.

What's next?
************

Now that you are familiar with ``PyAnnote`` foundation objects, I encourage you to have a look at the API to know a bit more about available algorithms and evaluation metrics.

Here is a short example.

Suppose you have lots of training data for speaker identification and that you are quite confident about the results it provides.
Yet, for various reason, you could not gather any annotated data for face recognition and therefore could not build any face models.
However, your face detection, tracking and clustering systems is quite robust as well.

	>>> face = Annotation(multitrack=True, video='MyVideo.avi', modality='face')
	>>> face[Segment(0, 4), 'face1'] = 'person1'
	>>> face[Segment(4, 15), 'face1'] = 'person1'
	>>> face[Segment(4, 15), 'face2'] = 'person2'
	>>> face[Segment(15, 17), 'face1'] = 'person2'
	>>> face[Segment(15, 17), 'face2'] = 'person3'
	>>> face[Segment(17, 25), 'face1'] = 'person1'
	>>> face[Segment(23, 30), 'face1'] = 'person2'

Why not try to recognize faces based on audio data only?, based on the co-occurrence of face clusters and speaker speech turns.

	>>> from pyannote.algorithm.mapping import HungarianMapper
	>>> mapper = HungarianMapper()
	>>> mapping = mapper(face, speaker)
	>>> print mapping
	(
	   person2 <--> Bob
	   person1 <--> Alice
	   person3 <--> 
	)
	>>> print face % mapping
	[
	   [0 --> 4] face1 : Alice
	   [4 --> 15] face1 : Alice
	              face2 : Bob
	   [15 --> 17] face1 : Bob
	               face2 : person3
	   [17 --> 25] face1 : Alice
	   [23 --> 30] face1 : Bob
	]
	