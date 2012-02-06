#!/usr/bin/env python
# encoding: utf-8

from ..generic import GenericParser

class MDTMParser(GenericParser):
    """
    .mdtm file parser
    """
    def __init__(self, path2mdtm):
        
        # source 1 start duration modality confidence subtype identifier
        format = '{VIDEO} {NA} {START} {DURATION} {MODALITY} {NA} {NA} {ID}' 
        super(MDTMParser, self).__init__(path2mdtm, \
                                         format, \
                                         multitrack = False)

class MDTMSample(MDTMParser):
    def __init__(self):
        import os.path
        sample_mdtm = '%s/../data/sample.mdtm' % (os.path.dirname(__file__))
        super(MDTMSample, self).__init__(sample_mdtm)

# def toMDTM(annotation):
#     """Meta Data Time-Mark"""
#     modality = annotation.modality
#     video    = annotation.video
#     text = ''
#     for s, segment in enumerate(annotation):
#         start = segment.start
#         duration = segment.duration
#         for i, identifier in enumerate(annotation.identifiers(segment=segment)):
#             confidence = annotation.confidence(segment, identifier)
#             # source 1 start duration modality confidence subtype identifier
#             text += '%s 1 %g %g %s %g %s %s\n' % (video, start, duration, modality, confidence, 'unknown', identifier)
#     return text
# 
# 
