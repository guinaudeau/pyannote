.. currentmodule:: pyannote

==========
Annotation
==========

Create empty annotation for video 'MyMovie.avi' and modality 'speaker'::

	>>> from pyannote import *
	>>> confidence = IDAnnotation(video='MyVideo.avi', modality='speaker')

An annotation is said to be empty in case it contains no annotated segment::

	>>> if not confidence:
	...     print 'Annotation is empty.'
	Annotation is empty.

Get/update video and modality attributes::

	>>> video = confidence.video
	>>> confidence.video = 'MyVideo.avi'
	>>> print confidence.modality
	speaker
   
Add annotation for given speech turn::
   
	>>> speech_turn = Segment(0, 10)
	>>> confidence[speech_turn, 'Paul'] = 0.99 
	>>> confidence[speech_turn, 'Patrick'] = 0.88
	>>> confidence[speech_turn, 'Bernard'] = 0.37
	

Get list of identifiers with at least one occurrence::

    >>> print confidence.IDs
	['Patrick', 'Paul', 'Bernard']

Add a few other occurrences of 'Paul' speaker::

	>>> confidence[Segment(15, 20), 'Paul'] = 0.78
	>>> confidence[Segment(40, 51), 'Paul'] = 0.89

Get annotation timeline::

	>>> print confidence.timeline
	[
	   [0 --> 10]
	   [15 --> 20]
	   [40 --> 51]
	]

Get annotation for a given segment::

    >>> print confidence[speech_turn]
	{'Patrick': 0.88, 'Paul': 0.99, 'Bernard': 0.37}

Sub-annotations
---------------

Sub-annotations can be obtained the same way sub-timelines are (see timeline tutorial)::

    >>> requested_segment = Segment(20, 45)
	>>> mode = 'loose' # or 'strict' or 'intersection'
    >>> subannotation = confidence(requested_segment, mode=mode)

Additionnaly, one can get annotation for a given identifier::

    >>> paul = confidence('Paul')
	
and then loop on annotated segments::	
	
	>>> for s, segment in enumerate(paul):
	...     print segment, paul[segment, 'Paul']


Translation
-----------
    



    # Add new track named name to segment
    segment = Segment( start_time, end_time )
    name = 'track name'
    track = TrackClass( args )    
    A[segment, name] = track
    
    # Add multiple new named tracks to segment
    named_tracks = {'first track name': track1, 
                    'other track name': track2, 
                    'final track name': track3}
    A[segment] = named_tracks
    
    # Get just added track back
    track = A[segment, name]
    
    # Get all tracks for segment
    # as a dictionary {'name': track}
    tracks = A[segment]
    
    # Remove just added track
    del A[segment, name]
    
    # Remove all tracks for segment
    del A[segment]

    # Remove all tracks for all segments
    A.clear()
    
    # Iterate through segments
    for s, segment in enumerate(A):
        # do something with A and segment
        pass
        
    A(segment)
    A(timeline)
    
    A ** timeline
    abs(A)
    
