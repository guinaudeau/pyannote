#!/usr/bin/env python
# encoding: utf-8

from ..generic import GenericParser

class REPEREParser(GenericParser):
    """
    .repere file parser
    """
    def __init__(self, path2repere, confidence=True, multitrack=False):
        # source start end modality identifier confidence
        if confidence:
            format = '{VIDEO} {START} {END} {MODALITY} {ID} {CONFIDENCE}'
        else:
            format = '{VIDEO} {START} {END} {MODALITY} {ID}'
        super(REPEREParser, self).__init__(path2repere, \
                                         format, \
                                         multitrack = multitrack)




# def toREPERE(annotation, confidence=False):
#     """"""
#     modality = annotation.modality
#     video    = annotation.video
#     text = ''
#     annotation = abs(annotation)
#     for s, segment in enumerate(annotation):
#         start = segment.start
#         end = segment.end
#         for i, identifier in enumerate(annotation.identifiers(segment=segment)):
#             if confidence:
#                 score = annotation.confidence(segment, identifier)
#                 # source start end modality identifier confidence
#                 text += '%s %g %g %s %s %g\n' % (video, start, end, modality, identifier, score)
#             else:
#                 text += '%s %g %g %s %s\n' % (video, start, end, modality, identifier)
#     return text


