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


from pyannote.parser.base import BaseAnnotationParser
from pyannote.parser.repere.idx import IDXParser
from pyannote.base.segment import Segment, SEGMENT_PRECISION
from lxml import objectify
import re

class XGTFParser(BaseAnnotationParser):
    
    def __init__(self):
        multitrack = True
        super(XGTFParser, self).__init__(multitrack)
        self.__idx = IDXParser()
    
    def _parse_frame(self, element):
        
        string = element.get('framespan')
        if not string:
            return Segment()
        
        p = re.compile('([0-9]*):([0-9]*)')
        m = p.match(string)
        return self.__idx[int(m.group(1))]
    
    def _parse_head(self, vpr):
        return [vpr.getchildren()[0].get('value')]
    
    def _parse_time(self, vpr):
        return self.__idx(int(vpr.getchildren()[0].get('value')))
    
    def _parse_written(self, vpr, alone=False):
        
        string = vpr.getchildren()[0].get('value')
        if not string:
            return []
            
        labels = []
        if alone:
            #         group  #1         #2         #3     #4
            p = re.compile('(.*?)<pers=(.*?)>.*?(</pers>)(.*)', re.DOTALL)
            m = p.match(string)
            while(m):
                beforeOnSameLine = m.group(1).split('\\n')[-1].strip()
                afterOnSameLine = m.group(4).split('\\n')[0].strip()
                if beforeOnSameLine == '' and afterOnSameLine == '':
                    labels.append(str(m.group(2)))
                string = string[m.end(3):]
                m = p.match(string)
        else:
            p = re.compile('.*?<pers=(.*?)>.*?</pers>', re.DOTALL)
            m = p.match(string)
            while(m):
                labels.append(str(m.group(1)))
                string = string[m.end():]
                m = p.match(string)
        
        return labels
    
    def read(self, path_xgtf, path_idx, video=None):
        
        # frame <--> timestamp mapping
        self.__idx.read(path_idx)
        
        # objectify xml file and get root
        root = objectify.parse(path_xgtf).getroot().data.sourcefile
        
        if video is None:
            video = root.get('filename')
        
        head = []
        written = []
        written_alone = []
        
        for element in root.iterchildren():
            
            frame_segment = self._parse_frame(element)
            if frame_segment and frame_segment not in self(video, "annotated"):
                self._add(frame_segment, "_", "_", video, "annotated")
            
            if element.get('name') in ['PERSONNE', 'TEXTE']:
                
                for vpr in element.iterchildren():
                    
                    attr_name = vpr.get('name')
                    if attr_name == 'STARTFRAME':
                        element_start = self._parse_time(vpr)
                    elif attr_name == 'ENDFRAME':
                        element_end = self._parse_time(vpr)
                    elif attr_name == 'TRANSCRIPTION':
                        written_alone = self._parse_written(vpr, alone=True)
                        written = self._parse_written(vpr, alone=False)
                    elif attr_name == 'NOM':
                        head = self._parse_head(vpr)
                
                element_segment = Segment(start=element_start, end=element_end)
                
                for modality, new_lbls in {'written (alone)' : written_alone,
                                           'written' : written, 
                                           'head' : head}.iteritems():
                    for lbl in new_lbls:
                        lbls = self(video, modality).get_labels(element_segment)
                        if lbl not in lbls:
                            self._add(element_segment, None, lbl, 
                                      video, modality)
        
        
        
        return self

if __name__ == "__main__":
    import doctest
    doctest.testmod()

