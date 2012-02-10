#!/usr/bin/env python
# encoding: utf-8

from ..generic import GenericParser
from pyannote import TrackIDAnnotation

class MDTMParser(GenericParser):
    """
    .mdtm file parser
    """
    def __init__(self, path2mdtm, multitrack=False):
        
        # source 1 start duration modality confidence subtype identifier
        format = '{VIDEO} {NA} {START} {DURATION} {MODALITY} {NA} {NA} {ID}' 
        super(MDTMParser, self).__init__(path2mdtm, \
                                         format, \
                                         multitrack = multitrack)

class MDTMSample(MDTMParser):
    def __init__(self):
        import os.path
        sample_mdtm = '%s/../data/sample.mdtm' % (os.path.dirname(__file__))
        super(MDTMSample, self).__init__(sample_mdtm)


def toMDTM(annotation, confidence=None):
    """
    Meta Data Time-Mark
    .. currentmodule:: pyannote
    
    :param annotation: annotation to be converted to MDTM format 
    :type annotation: :class:`TrackIDAnnotation` or :class:`IDAnnotation`
    :param confidence: function that takes annotation[s, t, i] as input and return confidence value
    :type confidence: function

    :returns: string containing annotation in MDTM format
    """

    if not isinstance(annotation, TrackIDAnnotation):
        raise TypeError('')
    
    annotation = annotation.toTrackIDAnnotation()
    
    if confidence is None:
        confidence = (lambda x: 1)
    
    modality = annotation.modality
    video    = annotation.video
    text = ''
        
    for segment in annotation:
        start = segment.start
        duration = segment.duration    
        for track in annotation[segment]:
            for identifier in annotation[segment, track]:
                score = confidence(annotation[segment, track, identifier])
                # source 1 start duration modality confidence subtype identifier
                text += '%s 1 %g %g %s %g %s %s\n' % (video, start, duration, modality, score, track, identifier)
                    
    return text


