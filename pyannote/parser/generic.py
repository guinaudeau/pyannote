#!/usr/bin/env python
# encoding: utf-8

# Copyright 2012 Herve BREDIN (bredin@limsi.fr)

# This file is part of PyAnnote.
# 
#     PyAnnote is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     PyAnnote is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with PyAnnote.  If not, see <http://www.gnu.org/licenses/>.

from pyannote.base.annotation import Annotation
from pyannote.base.segment import Segment
from pyannote.base.feature import SlidingWindow

# class GenericParser(object):
#     """
#     """
#     def __init__(self, path2file, \
#                        format, \
#                        multitrack = True, \
#                        auto_track_prefix = 'track', \
#                        default_confidence = True, \
#                        sliding_window = None, \
#                        video = None, \
#                        modality = None, \
#                        ):
#         """
#     :param path2file: path to parsed file
#     :param format: string with place-holders describing each line
#                    of the file -- available place-holders are
#                    {VIDEO} for video name
#                    {START} for start time
#                    {END} for end time
#                    {DURATION} for segment duration
#                    {TRACK} for track name
#                    {MODALITY} for modality name
#                    {ID} for identifier
#                    {CONFIDENCE} for confidence score
#     :param multitrack: whether annotation is multi-track
#                        (default is mono-track) 
#     :param auto_track_prefix: in case track name cannot be retrieved from line
#                               use this prefix to generate one automatically
#     :param default_confidence: what to put as confidence value if it cannot be
#                                retrieved from line
#     :param sliding_window: when provided, start/end times and duration are 
#                            considered as number of frames -- and sliding window
#                            toSegment method is used to convert them to seconds.
#     :param video: in case video name cannot be retrieved from line, 
#                   use this default value
#     :param modality: in case modality name cannot be retrieved from line,
#                      use this default value
# 
#     :rtype: GenericParser        
#         """
#         
#         super(GenericParser, self).__init__()
#         
#         # -------------------------------------------------------#
#         
#         self.path2file = path2file
#         self.format = format
#         self.multitrack = multitrack
#         self.auto_track_prefix = auto_track_prefix
#         self.default_confidence = default_confidence
#         self.sliding_window = sliding_window
#         self.video = video
#         self.modality = modality
#         
#         # -------------------------------------------------------#
#         
#         fields = self.format.split()
#         position = {}
#         
#         try:
#             position['id']  = fields.index('{ID}')
#         except:
#             raise ValueError('No {ID} placeholder in provided format.')
#         
#         try:
#             position['video'] = fields.index('{VIDEO}')
#         except:
#             position['video'] = -1
#         
#         try:
#             position['modality'] = fields.index('{MODALITY}')
#         except:
#             position['modality'] = -1
# 
# 
#         try:
#             position['track'] = fields.index('{TRACK}')
#         except:
#             position['track'] = -1
# 
#         try:
#             position['start'] = fields.index('{START}')
#         except:
#             position['start'] = -1
#         
#         try: 
#             position['duration'] = fields.index('{DURATION}')
#         except:
#             position['duration'] = -1
#             
#         try:
#             position['end'] = fields.index('{END}')
#         except:
#             position['end'] = -1
#         
#         if position['duration'] < 0 and position['end'] < 0:
#             raise ValueError('You must provide at least one of '\
#                              '{DURATION} or {END} placeholder')
#                              
#         try:
#             position['confidence'] = fields.index('{CONFIDENCE}')
#         except:
#             position['confidence'] = -1
#             
#         self.position = position
#                 
#         # -------------------------------------------------------#
# 
#         # empty list of annotations
#         self.annotations = {}
#         
#         # parse file
#         f = open(self.path2file, 'r')
#         for line in f:
#             
#             # skip comments
#             if line[0] == '#':
#                 continue
#             
#             # split line into fields
#             fields = line.split()
#             
#             # get video from line
#             # or use the one provided by the user
#             # if none is available
#             if self.position['video'] < 0:
#                 video = self.video
#             else:
#                 video = fields[self.position['video']]
#             
#             # get modality from line
#             # or use the one provided by the user
#             # if none is available
#             if self.position['modality'] < 0:
#                 modality = self.modality
#             else:
#                 modality = fields[self.position['modality']]
#             
#             # get identifier from line
#             identifier = fields[self.position['id']]
# 
#             # get segment from line
#             # if sliding window is provided, 
#             # provided numbers are expected to be number of frames
#             if self.sliding_window:
#                 start = int(fields[self.position['start']])
#                 if self.position['duration'] < 0:
#                     duration = int(fields[self.position['end']]) - start
#                 else:
#                     duration = int(fields[self.position['duration']])
#                 segment = self.sliding_window.toSegment(start, duration)
#             
#             
#             # if sliding window is **not** provided
#             # provided numbers are expected to be timestamps in seconds
#             else:
#                 start = float(fields[self.position['start']])
#                 if self.position['end'] < 0:
#                     end = start + float(fields[self.position['duration']])
#                 else:
#                     end = float(fields[self.position['end']])
#                 segment = Segment(start, end)
#             
#             if self.position['confidence'] < 0:
#                 confidence = self.default_confidence
#             else:
#                 confidence = float(fields[self.position['confidence']])
#             
#             # create empty annotation if video was never seen before
#             # or if modality was never seen before for this video
#             if video not in self.annotations:
#                 self.annotations[video] = {}
#             if modality not in self.annotations[video]:
#                 # dependning on the value of multitrack parameter
#                 # provided by the user, create a (multi-track) Annotation
#                 # or an (mono-track) Annotation
#                 if self.multitrack:
#                     self.annotations[video][modality] = \
#                         Annotation(modality=modality, video=video)
#                 else:
#                     self.annotations[video][modality] = \
#                         Annotation(modality=modality, video=video)
#             
#             # if we're dealing with multi-track Annotation
#             if self.multitrack:
#                 
#                 # case 1: track name cannot be read from the line
#                 # ==> generate a new one
#                 if self.position['track'] < 0:
#                     track = self.annotations[video][modality]\
#                                 .auto_track_name(segment, \
#                                                  prefix=self.auto_track_prefix)
#                 # case 2: track can be read from the line
#                 # ==> read it, pardi !
#                 else:
#                     track = fields[self.position['track']]
#                 
#                 # add identifier to this track
#                 self.annotations[video][modality][segment, \
#                                                   track, \
#                                                   identifier] = confidence
#             else:
#                 self.annotations[video][modality][segment, identifier] = \
#                                                                 confidence
#         
#     def annotation(self, video, modality):
#         
#         if (video in self.annotations) and (modality in self.annotations[video]):
#             return self.annotations[video][modality]
#         else:
#             if self.multitrack:
#                 return Annotation(modality=modality, video=video)
#             else:
#                 return Annotation(modality=modality, video=video)
#             
#     def timeline(self, video, modality):
#         return self.annotation(video, modality).timeline
#         
#     def videos(self):
#         return self.annotations.keys()
#     
#     def modalities(self, video):
#         if video in self.annotations:
#             return self.annotations[video].keys()
#         else:
#             return []
# 

class GenericParser(object):
    """
    """
    def __init__(self, path2file, \
                       format, \
                       multitrack = True, \
                       auto_track_prefix = 'track', \
                       default_confidence = True, \
                       sliding_window = None, \
                       video = None, \
                       modality = None, \
                       ):
        """
    :param path2file: path to parsed file
    :param format: string with place-holders describing each line
                   of the file -- available place-holders are
                   {VIDEO} for video name
                   {START} for start time
                   {END} for end time
                   {DURATION} for segment duration
                   {TRACK} for track name
                   {MODALITY} for modality name
                   {ID} for identifier
                   {CONFIDENCE} for confidence score
    :param multitrack: whether annotation is multi-track
                       (default is mono-track) 
    :param auto_track_prefix: in case track name cannot be retrieved from line
                              use this prefix to generate one automatically
    :param default_confidence: what to put as confidence value if it cannot be
                               retrieved from line
    :param sliding_window: when provided, start/end times and duration are 
                           considered as number of frames -- and sliding window
                           toSegment method is used to convert them to seconds.
    :param video: in case video name cannot be retrieved from line, 
                  use this default value
    :param modality: in case modality name cannot be retrieved from line,
                     use this default value

    :rtype: GenericParser        
        """
        
        super(GenericParser, self).__init__()
        
        # -------------------------------------------------------#
        
        self.path2file = path2file
        self.format = format
        self.multitrack = multitrack
        self.auto_track_prefix = auto_track_prefix
        self.default_confidence = default_confidence
        self.sliding_window = sliding_window
        self.video = video
        self.modality = modality
        
        # -------------------------------------------------------#
        
        fields = self.format.split()
        position = {}
        
        try:
            position['id']  = fields.index('{ID}')
        except:
            raise ValueError('No {ID} placeholder in provided format.')
        
        try:
            position['video'] = fields.index('{VIDEO}')
        except:
            position['video'] = -1
        
        try:
            position['modality'] = fields.index('{MODALITY}')
        except:
            position['modality'] = -1


        try:
            position['track'] = fields.index('{TRACK}')
        except:
            position['track'] = -1

        try:
            position['start'] = fields.index('{START}')
        except:
            position['start'] = -1
        
        try: 
            position['duration'] = fields.index('{DURATION}')
        except:
            position['duration'] = -1
            
        try:
            position['end'] = fields.index('{END}')
        except:
            position['end'] = -1
        
        if position['duration'] < 0 and position['end'] < 0:
            raise ValueError('You must provide at least one of '\
                             '{DURATION} or {END} placeholder')
                             
        try:
            position['confidence'] = fields.index('{CONFIDENCE}')
        except:
            position['confidence'] = -1
            
        self.position = position
                
        # -------------------------------------------------------#

        # empty list of annotations
        self.annotations = {}
        
        # parse file
        f = open(self.path2file, 'r')
        for line in f:
            
            # skip comments
            if line[0] == '#':
                continue
            
            # split line into fields
            fields = line.split()
            
            # get video from line
            # or use the one provided by the user
            # if none is available
            if self.position['video'] < 0:
                video = self.video
            else:
                video = fields[self.position['video']]
            
            # get modality from line
            # or use the one provided by the user
            # if none is available
            if self.position['modality'] < 0:
                modality = self.modality
            else:
                modality = fields[self.position['modality']]
            
            # get identifier from line
            identifier = fields[self.position['id']]

            # get segment from line
            # if sliding window is provided, 
            # provided numbers are expected to be number of frames
            if self.sliding_window:
                start = int(fields[self.position['start']])
                if self.position['duration'] < 0:
                    duration = int(fields[self.position['end']]) - start
                else:
                    duration = int(fields[self.position['duration']])
                segment = self.sliding_window.toSegment(start, duration)
            
            
            # if sliding window is **not** provided
            # provided numbers are expected to be timestamps in seconds
            else:
                start = float(fields[self.position['start']])
                if self.position['end'] < 0:
                    end = start + float(fields[self.position['duration']])
                else:
                    end = float(fields[self.position['end']])
                segment = Segment(start, end)
            
            if self.position['confidence'] < 0:
                confidence = self.default_confidence
            else:
                confidence = float(fields[self.position['confidence']])
            
            # create empty annotation if video was never seen before
            # or if modality was never seen before for this video
            if video not in self.annotations:
                self.annotations[video] = {}
            if modality not in self.annotations[video]:
                self.annotations[video][modality] = \
                    Annotation(multitrack=self.multitrack, \
                            video=video, modality=modality)
            
            # if we're dealing with multi-track tag
            if self.multitrack:
                
                # case 1: track name cannot be read from the line
                # ==> generate a new one
                if self.position['track'] < 0:
                    track = self.annotations[video][modality]\
                            .new_track(segment, prefix=self.auto_track_prefix)
                # case 2: track can be read from the line
                # ==> read it, pardi !
                else:
                    track = fields[self.position['track']]
                
                # add label to this track
                self.annotations[video][modality][segment, track] = identifier
            else:
                self.annotations[video][modality][segment] = identifier
        
    def annotation(self, video, modality):
        
        if (video in self.annotations) and \
           (modality in self.annotations[video]):
            return self.annotations[video][modality]
        else:
            return Annotation(multitrack=self.multitrack, \
                           video=video, modality=modality)
            
    def timeline(self, video, modality):
        return self.annotation(video, modality).timeline
        
    def videos(self):
        return self.annotations.keys()
    
    def modalities(self, video):
        if video in self.annotations:
            return self.annotations[video].keys()
        else:
            return []
            
if __name__ == "__main__":
    import doctest
    doctest.testmod()
