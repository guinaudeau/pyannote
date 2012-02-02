#!/usr/bin/env python
# encoding: utf-8

import numpy as np
from generic import GenericParser
from ..base import IDAnnotation

class TVTParser(GenericParser):
    def __init__(self, path2tvt):
        
        format = '{VIDEO} {START} {DURATION} {TRACK} {ID} {CONFIDENCE}'
        super(TVTParser, self).__init__(path2tvt, \
                                         format, \
                                         multitrack = True)
        # annotation will follow this format
        # annotation[segment, track, other_track] = distance_to_other_track
        # where segment is track segment


# class TVTParser(object):
#     """
#     .tvt (track vs. track) file parser
#     """
#     def __init__(self, path2tvt):
#         
#         super(TVTParser, self).__init__()
#         self.path2tvt = path2tvt
#         
#         # empty list of tvts
#         self.tvts = {}
#         
#         # parse file
#         f = open(self.path2tvt, 'r')
#         for line in f:
#             # split line into fields
#             
#             # BFMTV_BFMStory_2011-05-11_175900 1.07 1.36 head_3 head_4 32.03
#             # {VIDEO} {START} {DURATION} {TRACK} {IDENTIFIER} {CONFIDENCE}
# 
#             fields = line.strip().split()
#             video = fields[0]
#             start = float(fields[1])
#             duration = float(fields[2])
#             track = fields[3]
#             other_track = fields[4]
#             distance = float(fields[5])
#             
#             if video not in self.tvts:
#                 a = Annotation(video=video)
#                 self.tvts[video] = {'tracks': a, 'distance': {} }            
#             
#             if track not in self.tvts[video]['tracks'].identifiers():
#                 segment = Segment(start, start+duration)
#                 self.tvts[video]['tracks'].add(segment, track)
#                 self.tvts[video]['distance'][track] = {}
#                 
#             self.tvts[video]['distance'][track][other_track] = distance
#     
#     def videos(self):
#         return self.tvts.keys()
# 
    def tracks(self, video):
        """
        Return IDAnnotation with multiple 
        """    
        
        a = self.annotations[video][None]
        t = IDAnnotation(video=video, modality=None)
        for segment in a:
            t[segment] = {name: True for name in a[segment].keys()}
        return t

    
    def matrix(self, video):
        
        t = self.tracks(video)
        track2index = {track:i for i, track in enumerate(t.IDs)}
        
        n = len(track2index)
        M = np.zeros((n, n))

        a = self.annotations[video][None]
        for segment in a:
            tracks = a[segment]
            for track in tracks:
                i = track2index[track]
                for other_track in tracks[track]:
                    j = track2index[other_track]
                    M[i, j] = tracks[track][other_track]
        
        return M
        
        
