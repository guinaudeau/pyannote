#!/usr/bin/env python
# encoding: utf-8

from generic import GenericParser

class MDTMParser(GenericParser):
    """
    .mdtm file parser
    """
    def __init__(self, path2mdtm):
        
        # source 1 start duration modality confidence subtype identifier
        format = '{VIDEO} {NA} {START} {DURATION} {MODALITY} {CONFIDENCE} {NA} {ID}' 
        super(MDTMParser, self).__init__(path2mdtm, \
                                         format, \
                                         multitrack = False)

# class MDTMParser(object):
#     """
#     .mdtm file parser
#     """
#     def __init__(self, path2mdtm, \
#                        modality=None, \
#                        sliding_window=None, \
#                        ):
#         
#         super(MDTMParser, self).__init__()
#         self.path2mdtm = path2mdtm
#         
#         # store modality
#         self.modality = modality
#         
#         # if sliding_window is provided, store it for later use
#         # otherwise, assumes .mdtm files contains timestamps and duration in seconds
#         # (rather than frame id and number)
#         self.sliding_window = sliding_window
#         
#         # empty list of annotations
#         self.mdtms = {}
#         
#         # parse file
#         f = open(self.path2mdtm, 'r')
#         for line in f:
#             
#             # skip comments
#             if line[0] == '#':
#                 continue
#             
#             # split line into fields
#             fields = line.split()
#             video = fields[0]
#             # _A = fields[1]
#             raw_i = fields[2]
#             raw_n = fields[3]
#             # _type = fields[4]
#             # _confidence = fields[5]
#             # _subtype = fields[6]
#             identifier = fields[7]
#             
#             # create empty annotation if new video
#             if video not in self.mdtms:
#                 self.mdtms[video] = Annotation(modality=self.modality, video=video)
#             
#             # compute Segment
#             if self.sliding_window is not None:
#                 segment = self.sliding_window.toSegment(int(raw_i) - 1, int(raw_n))
#             else:
#                 segment = Segment(float(raw_i), float(raw_i) + float(raw_n))
#             
#             self.mdtms[video].add(segment, identifier, attributes={}, confidence=1.)
#     
#     def annotation(self, video):
#         return self.mdtms[video]
#     
#     def timeline(self, video):
#         return self.mdtms[video].timeline
#         
#     def videos(self):
#         return self.mdtms.keys()
# 

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
