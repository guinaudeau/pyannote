#!/usr/bin/env python
# encoding: utf-8

from ..generic import GenericParser

class ETF0Parser(GenericParser):
    """
    .etf0 file parser
    """
    def __init__(self, path2etf0):
        
        format = '{VIDEO} {NA} {START} {DURATION} {MODALITY} {NA} {ID} {CONFIDENCE} {NA}' 
        super(ETF0Parser, self).__init__(path2etf0, \
                                         format, \
                                         multitrack = False)

class ETFParser(GenericParser):
    """
    .etf file parser
    """
    def __init__(self, path2etf):
        
        format = '{VIDEO} {NA} {START} {DURATION} {MODALITY} {NA} {ID} {CONFIDENCE} {NA}' 
        super(ETFParser, self).__init__(path2etf, \
                                         format, \
                                         multitrack = False)


# def toETF(annotation):
#     """"""
#     modality = annotation.modality
#     video    = annotation.video
#     text = ''
#     for s, segment in enumerate(annotation):
#         start = segment.start
#         duration = segment.duration
#         for i, identifier in enumerate(annotation.identifiers(segment=segment)):
#             confidence = annotation.confidence(segment, identifier)
#             # source 1 start duration type subtype event [score [decision]]
#             text += '%s 1 %g %g %s - %s %g -\n' % (video, start, duration, modality, identifier, confidence)
#     return text


