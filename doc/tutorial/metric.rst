.. currentmodule:: pyannote

======
Metric
======

    >>> from pyannote import *

    >>> reference = IDAnnotation(video='MyVideo.avi', modality='speaker')
    >>> reference[Segment(0, 10), 'Bernard'] = True
    >>> reference[Segment(9, 15), 'Albert'] = True
    >>> reference[Segment(15, 20), 'Jean'] = True
    >>> reference[Segment(20, 30), 'Bernard'] = True
    >>> reference[Segment(29, 33), 'Jean'] = True
    >>> reference[Segment(33, 40), 'Albert'] = True

    >>> hypothesis = IDAnnotation(video='MyVideo.avi', modality='speaker')
    >>> hypothesis[Segment(1, 11), 'speaker#1'] = True
    >>> hypothesis[Segment(21, 31), 'speaker#1'] = True
    >>> hypothesis[Segment(9, 15), 'speaker#2'] = True
    >>> hypothesis[Segment(29, 33), 'speaker#2'] = True
    >>> hypothesis[Segment(15, 20), 'speaker#3'] = True
    >>> hypothesis[Segment(33, 40), 'speaker#2'] = True
    >>> hypothesis[Segment(40, 41), 'speaker#4'] = True
    
Detection error rate
--------------------
	
	>>> from pyannote.metric.detection import DetectionErrorRate
	>>> der = DetectionErrorRate()
	>>> print der(reference, hypothesis, detailed=True)
	{'false alarm': 3.0, 'total': 42.0, 'miss': 2.0, 'detection error rate': 0.11904761904761904}
	
Diarization error rate
----------------------

	>>> from pyannote.metric.diarization import DiarizationErrorRate
	>>> der = DiarizationErrorRate()
	>>> print der(reference, hypothesis, detailed=True)
	{'diarization error rate': 0.21428571428571427, 'false alarm': 3.0, 'confusion': 4.0, 'total': 42.0, 'miss': 2.0, 'correct': 36.0}
	
Identification error rate
-------------------------

	>>> from pyannote.algorithms.association.hungarian import Hungarian
	>>> mapper = Hungarian()
	>>> mapping = mapper(hypothesis, reference)
	>>> print mapping
	{('speaker#2',): ('Albert',), ('speaker#4',): Ø, ('speaker#1',): ('Bernard',), ('speaker#3',): ('Jean',)}
	
	>>> from pyannote.metric.identification import IdentificationErrorRate
	>>> ier = IdentificationErrorRate()
	>>> print ier(reference, hypothesis % mapping, detailed=True)
	{'identification error rate': 0.21428571428571427, 'false alarm': 3.0, 'confusion': 4.0, 'total': 42.0, 'miss': 2.0, 'correct': 36.0}

