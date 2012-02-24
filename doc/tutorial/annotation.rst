.. currentmodule:: pyannote

==========
Annotation
==========

Let us start with a simple type of annotations: :class:`IDAnnotation`.
It can be used, for instance, to store the output of a speaker identification system.

Here is how to create an empty :class:`IDAnnotation` for video 'MyMovie.avi' and modality 'speaker'::

	>>> from pyannote import *
	>>> S = IDAnnotation(video='MyVideo.avi', modality='speaker')

The most basic way of using is to store one segment per speech turn and annotate
it with the recognized speaker identifier.

Add annotation for given speech turn::
   
	>>> speech_turn = Segment(0, 10)
	>>> S[speech_turn, 'Paul'] = 0.99 

As you can see above, speaker called 'Paul' was recognized with a probability of 0.99.
Obviously, you are not restricted to store only one of those probabilities. 

	>>> S[speech_turn, 'Patrick'] = 0.88
	>>> S[speech_turn, 'Bernard'] = 0.37
 
If necessary, you can get back the list of identifiers appearing at least once
in the whole annotation.

    >>> print S.IDs
    ['Patrick', 'Paul', 'Bernard']

Here is how to get the data back from S::

	>>> S[speech_turn]
	{'Patrick': 0.88, 'Paul': 0.99, 'Bernard': 0.37}
 
Also, we could have stored any other information using a dictionary::

	>>> S[speech_turn, 'Paul'] = {'confidence':0.99, 'gender': 'male'}

For the purpose of this tutorial, we will keep it simple::

	>>> S[speech_turn, 'Paul'] = 0.99
	>>> del S[speech_turn, 'Patrick']
	>>> del S[speech_turn, 'Bernard']

Add a few other occurrences of 'Paul' speaker and others::

	>>> S[Segment(15, 20), 'Paul'] = 0.78
	>>> S[Segment(20, 30), 'Bernard'] = 0.89
	>>> S[Segment(30, 38), 'Patrick'] = 0.67
	>>> S[Segment(40, 51), 'Paul'] = 0.89

Get annotation timeline::

	>>> print S.timeline
	[
	   [0 --> 10]
	   [15 --> 20]
	   [20 --> 30]
	   [30 --> 38]
	   [40 --> 51]
	]

Sub-annotations
---------------

Sub-annotations can be obtained the same way sub-timelines are (see timeline tutorial)::

    >>> requested_segment = Segment(20, 45)
    >>> s = S(requested_segment, mode='loose')
	>>> for segment in s:
	...     print segment, s[segment]
	[20 --> 30] {'Bernard': 0.89}
	[30 --> 38] {'Patrick': 0.67}
	[40 --> 51] {'Paul': 0.89}

Additionnaly, one can get annotation for a given identifier::

    >>> p = S('Paul')
	>>> for segment in p:
	...     print segment, p[segment]
	[0 --> 10] {'Paul': 0.99}
	[15 --> 20] {'Paul': 0.78}
	[40 --> 51] {'Paul': 0.89}
	>>> print 'Paul speaks during %g seconds.' % S('Paul').timeline.duration()
	Paul speaks during 26 seconds.

Have a look at :meth:`TrackIDAnnotation.__call__` for more details on sub-annotations.

Confusion, translation and tagging
----------------------------------

Confusion (or cooccurrence) matrix between two annotations can be obtained easily
via the * operator::
	
	>>> T = IDAnnotation(video='MyVideo.avi', modality='speaker')
	>>> T[Segment(0,20), 'Paul'] = 0.34
	>>> T[Segment(20, 60), 'Bernard'] = 0.89
	>>> confusion = T * S
	>>> confusion('Bernard')
	{'Bernard': 10.0, 'Paul': 11.0, 'Patrick': 8.0}
	>>> confusion['Bernard', 'Patrick']
	8.0

Identifiers can be translated easily. For instance, this can be useful to give
proper name to speaker clusters output by a speaker diarization system -- once
they are recognized::

	>>> translation = {'Bernard': 'Bernard_PIVOT', 'Paul': 'Paul_SIMON'}
	>>> Z = S % translation
	>>> print Z.IDs
	['Patrick', 'Bernard_PIVOT', 'Paul_SIMON']

Identifiers with no translation are kept as is.

Timeline tagging can be easily done using the >> operator::

	>>> T_tagged_by_S = S >> T.timeline

What it does is simply projecting (intersecting) annotation S onto each segment of T.

Multiple tracks
---------------

Class :class:`TrackIDAnnotation` can be seen as an extension of :class:`IDAnnotation` 
(though in Python practice, it is the other way around :class:`IDAnnotation` inherits
from :class:`TrackIDAnnotation`.)

The main difference is that it is meant to store multiple tracks per segment.
It might useful, for instance, when working on face recognition: multiple faces
can appear simultaneously on screen and we need to know which is which.

	>>> F = TrackIDAnnotation(video='MyVideo.avi', modality='face')
	>>> F[Segment(0, 15), 'head1', 'Paul'] = 0.87
	>>> F[Segment(0, 15), 'head2', 'Bernard'] = 0.67

Sub-annotations, confusion and translation can be used the same way.










    
