#!/usr/bin/env python
# encoding: utf-8

from generic import GenericParser

class REPEREParser(GenericParser):
    """
    .repere file parser
    """
    def __init__(self, path2repere):
        # source start end modality identifier confidence
        format = '{VIDEO} {START} {END} {MODALITY} {ID} {CONFIDENCE}'
        super(REPEREParser, self).__init__(path2repere, \
                                         format, \
                                         multitrack = False)


# class REPEREParser(object):
#     """
#     .repere file parser
#     """
#     def __init__(self, path2repere, \
#                        sliding_window=None, \
#                        ):
#         
#         super(REPEREParser, self).__init__()
#         self.path2repere = path2repere
#         
#         # if sliding_window is provided, store it for later use
#         # otherwise, assumes .repere files contains timestamps and duration in seconds
#         # (rather than frame id and number)
#         self.sliding_window = sliding_window
#         
#         # empty list of annotations
#         self.reperes = {}
#         
#         # parse file
#         f = open(self.path2repere, 'r')
#         for line in f:
#             
#             # skip comments
#             if line[0] == '#':
#                 continue
#             
#             # split line into fields
#             fields = line.split()
#             video = fields[0]
#             raw_i = fields[1]
#             raw_n = fields[2]
#             modality = fields[3]
#             identifier = fields[4]
#             
#             # create empty annotation if new video/modality
#             if video not in self.reperes:
#                 self.reperes[video] = {}
#             if modality not in self.reperes[video]:
#                 self.reperes[video][modality] = Annotation(modality=modality, video=video)
#                 
#             # compute Segment
#             if self.sliding_window is not None:
#                 segment = self.sliding_window.toSegment(int(raw_i) - 1, int(raw_n))
#             else:
#                 segment = Segment(float(raw_i), float(raw_n))
#             
#             self.reperes[video][modality].add(segment, identifier, attributes={}, confidence=1.)
#     
#     def annotation(self, video, modality):
#         return self.reperes[video][modality]
#     
#     def timeline(self, video, modality):
#         return self.reperes[video][modality].timeline
#         
#     def videos(self):
#         return self.reperes.keys()
#     
#     def modalities(self, video):
#         return self.reperes[video].keys()


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


