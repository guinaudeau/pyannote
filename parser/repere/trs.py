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

from pyannote import Segment, Timeline, TrackIDAnnotation
from lxml import objectify
import re

MODALITY_SPEAKER = 'speaker'
MODALITY_SPOKEN  = 'spoken'

class TRSParser(object):
    """
    .trs file parser
    """
    def __init__(self, path2trs, video=None):
        super(TRSParser, self).__init__()
        self.__trs = path2trs
        self.__xmlroot = objectify.parse(self.__trs).getroot()
        self.__name = {}
        self.__gender = {}
        for speaker in self.root.Speakers.iterchildren():
            self.__name[speaker.get('id')] = speaker.get('name')
            self.__gender[speaker.get('id')] = speaker.get('type')
        if video is None:
            self.__video = self.root.get('audio_filename')
        else:
            self.__video = video
    
    def __get_video(self): 
        return self.__video
    def __set_video(self, value):
        self.__video = value
    video = property(fget=__get_video, \
                     fset=__set_video, \
                     fdel=None, \
                     doc="Annotated video.")

    def __get_root(self): 
        return self.__xmlroot
    root = property(fget=__get_root, \
                     fset=None, \
                     fdel=None, \
                     doc="XML root.")
    
    def __extract_spoken(self, text):
        identifiers = []
        if text:
            p = re.compile('.*?<pers=(.*?)>.*?</pers>', re.DOTALL)
            m = p.match(text)
            while(m):
                # split Jean-Marie_LEPEN,Marine_LEPEN ("les LEPEN")
                for identifier in m.group(1).split(','):
                    identifiers.append(str(identifier))
                text = text[m.end():]
                m = p.match(text)
        
        return identifiers
        
    def __extract_speakers(self, text):
        identifiers = []
        if text:
            for i, identifier in enumerate(text.split()):
                identifiers.append(identifier)
        return identifiers

    def __fix_incomplete(self, incomplete, latest_sync):
        for s, segment in enumerate(incomplete):
            segment.end = latest_sync
        return []
    
    def transcribed(self, non_transcribed='nontrans'):
        timeline = Timeline(video=self.video)
        for section in self.root.Episode.iterchildren():
            if section.get('type') != non_transcribed:
                section_start = float(section.get('startTime'))
                section_end   = float(section.get('endTime'))
                segment = Segment(start=section_start, end=section_end)
                timeline += segment
        return timeline
                
    def speaker(self, name=True, ):
        annotation = TrackIDAnnotation(modality=MODALITY_SPEAKER, \
                                       video=self.video)
        # parse file looking for speaker info.
        for section in self.root.Episode.iterchildren():
            for turn in section.iterchildren():
                turn_start = float(turn.get('startTime'))
                turn_end   = float(turn.get('endTime'))
                segment = Segment(start=turn_start, end=turn_end)
                identifiers = self.__extract_speakers(turn.get('speaker'))
                for i, identifier in enumerate(identifiers):
                    track = annotation.auto_track_name(segment, prefix='speaker')
                    value = {'gender': self.__gender[identifier]}
                    if name:
                        annotation[segment, track, self.__name[identifier]] = value
                    else:
                        annotation[segment, track, identifier] = value

        return annotation
    
    def spoken(self, value=True):
        
        annotation = TrackIDAnnotation(modality=MODALITY_SPOKEN, \
                                       video=self.video)
        incomplete = []
        
        for section in self.root.Episode.iterchildren():
            section_start = float(section.get('startTime'))
            section_end   = float(section.get('endTime'))
            
            # ==> SYNC
            latest_sync = section_start
            incomplete = self.__fix_incomplete(incomplete, latest_sync)
            
            for turn in section.iterchildren():
                turn_start = float(turn.get('startTime'))
                turn_end   = float(turn.get('endTime'))
                
                # ==> SYNC
                latest_sync = turn_start
                incomplete = self.__fix_incomplete(incomplete, latest_sync)
                
                for element in turn.iterchildren():
                    if element.tag == 'Sync':
                        # ==> SYNC
                        latest_sync = float(element.get('time'))
                        incomplete = self.__fix_incomplete(incomplete, latest_sync)
                    
                    identifiers = self.__extract_spoken(element.tail)
                    segment = Segment(start=latest_sync, end=latest_sync+1e-3)
                    incomplete.append(segment)
                    
                    for i, identifier in enumerate(identifiers):
                        track = annotation.auto_track_name(segment, prefix='spoken')
                        annotation[segment, track, identifier] = value
                
                # ==> SYNC
                latest_sync = turn_end
                incomplete = self.__fix_incomplete(incomplete, latest_sync)
                
            # ==> SYNC
            latest_sync = section_end
            incomplete = self.__fix_incomplete(incomplete, latest_sync)
        
        return annotation
