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
from idx import IDXParser
from lxml import objectify
import re

MODALITY_HEAD = 'head'
MODALITY_WRITTEN = 'written'

class XGTFParser(object):
    """
    .xgtf file parser
    """
    def __init__(self, path2xgtf, path2idx, video=None):
        super(XGTFParser, self).__init__()
        self.__xgtf = path2xgtf
        self.__idx  = IDXParser(path2idx)
        self.__xmlroot = objectify.parse(self.__xgtf).getroot()
        if video is None:
            self.__video = self.root.get('filename')
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

    def __get_idx(self): 
        return self.__idx
    idx = property(fget=__get_idx, \
                     fset=None, \
                     fdel=None, \
                     doc="Frame index.")

    def __get_root(self): 
        return self.__xmlroot.data.sourcefile
    root = property(fget=__get_root, \
                     fset=None, \
                     fdel=None, \
                     doc="XML root.")
    
    def __extract_value(self, attr):
        return attr.getchildren()[0].get('value')

    def head(self, value=True):
        annotation = TrackIDAnnotation(modality=MODALITY_HEAD, \
                                       video=self.video)
        # parse file looking for face info.
        
        for element in self.root.iterchildren():
            # only add PERSONNE objects
            if element.get('name') != 'PERSONNE':
                continue
            
            for vpr_object in element.iterchildren():
                attr_name = vpr_object.get('name')
                if attr_name == 'STARTFRAME':
                    startframe = int(self.__extract_value(vpr_object))
                elif attr_name == 'ENDFRAME':
                    endframe = int(self.__extract_value(vpr_object))
                elif attr_name == 'NOM':
                    # sample:
                    # <attribute name="NOM">
                    #    <data:svalue value="Jerome_CAHUZAC"/>
                    # </attribute>
                    identifier = self.__extract_value(vpr_object)
                else:
                    pass
            segment = Segment(start=self.idx(startframe), \
                              end=self.idx(endframe))
            
            # faces are annotated every few seconds
            # therefore, two faces might belong to the same segment
            # make sure this is a new face in this segment 
            # before adding it to the annotation
            
            if identifier not in annotation.IDs or \
               segment not in annotation(identifier).timeline:
                # really sure this is a new face for this segment?
                # automatically generate track name (face0, face1, face2, ...)
                name = annotation.auto_track_name(segment, prefix='face')
                annotation[segment, name, identifier] = value
        
        return annotation
        
    def __extract_written(self, text, name_alone=False):
        """
        If name_alone is set to True, will only return identifiers that are
        not surrounded by other text on the same line.
        """
        identifiers = []
        if text:
            if name_alone:
                #         group  #1         #2         #3     #4
                p = re.compile('(.*?)<pers=(.*?)>.*?(</pers>)(.*)', re.DOTALL)
                m = p.match(text)
                while(m):
                    beforeOnSameLine = m.group(1).split('\\n')[-1].strip()
                    afterOnSameLine = m.group(4).split('\\n')[0].strip()
                    if beforeOnSameLine == '' and afterOnSameLine == '':
                        identifiers.append(m.group(2))
                    text = text[m.end(3):]
                    m = p.match(text)
            else:
                p = re.compile('.*?<pers=(.*?)>.*?</pers>', re.DOTALL)
                m = p.match(text)
                while(m):
                    identifiers.append(m.group(1))
                    text = text[m.end():]  
                    m = p.match(text)
        
        return identifiers
    
    def written(self, value=True, name_alone=False):
        annotation = TrackIDAnnotation(modality=MODALITY_WRITTEN, \
                                       video=self.video)

        for element in self.root.iterchildren():
            # only add PERSONNE objects
            if element.get('name') != 'TEXTE':
                continue
            
            for vpr_object in element.iterchildren():
                attr_name = vpr_object.get('name')
                if attr_name == 'STARTFRAME':
                    startframe = int(self.__extract_value(vpr_object))
                elif attr_name == 'ENDFRAME':
                    endframe = int(self__extract_value(vpr_object))
                elif attr_name == 'TRANSCRIPTION':
                    identifiers = \
                    self.__extract_written(self.__extract_value(vpr_object), \
                                           name_alone=name_alone)
                else:
                    pass
            segment = Segment(start=self.idx(startframe), end=self.idx(endframe))
            for i, identifier in enumerate(identifiers):
                if identifier not in annotation.IDs or \
                   segment not in annotation(identifier).timeline:
                    name = annotation.auto_track_name(segment, prefix='text')
                    annotation[segment, name, identifier] = value
        
        return annotation
    
    def annotated(self):
        """"""
        half_frame_duration = .5 * self.idx.delta
        timeline = Timeline(video=self.video)
        p = re.compile('([0-9]*):([0-9]*)')
        for element in self.root.iterchildren():
            text = element.get('framespan')
            if text:
                m = p.match(text)
                frame_time  = self.idx(int(m.group(1)))
                segment = Segment(start=frame_time - half_frame_duration, \
                                  end=frame_time + half_frame_duration)            
                timeline += segment
        
        return timeline        
