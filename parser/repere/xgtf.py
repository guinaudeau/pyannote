#!/usr/bin/env python
# encoding: utf-8

from pyannote import Segment, Timeline, TrackIDAnnotation
from idx import IDXParser
from lxml import objectify
import re

MODALITY_HEAD = 'head'
MODALITY_WRITTEN = 'written'

def _extract_value(attr):
    return attr.getchildren()[0].get('value')

def _extract_written(text, name_alone=False):
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

class XGTFParser(object):
    """
    .xgtf file parser
    """
    def __init__(self, path2xgtf, path2idx, video=None):
        super(XGTFParser, self).__init__()
        self._xgtf = path2xgtf
        self._idx  = IDXParser(path2idx)
        self._xmlroot = objectify.parse(self._xgtf).getroot()
        if video is None:
            self._video = self._xmlroot.data.sourcefile.get('filename')
        else:
            self._video = video
    
    def head(self, value=True):
        annotation = TrackIDAnnotation(modality=MODALITY_HEAD, \
                                       video=self._video)
        # parse file looking for face info.
        
        for element in self._xmlroot.data.sourcefile.iterchildren():
            # only add PERSONNE objects
            if element.get('name') != 'PERSONNE':
                continue
            
            for vpr_object in element.iterchildren():
                attr_name = vpr_object.get('name')
                if attr_name == 'STARTFRAME':
                    startframe = int(_extract_value(vpr_object))
                elif attr_name == 'ENDFRAME':
                    endframe = int(_extract_value(vpr_object))
                elif attr_name == 'NOM':
                    # sample:
                    # <attribute name="NOM">
                    #    <data:svalue value="Jerome_CAHUZAC"/>
                    # </attribute>
                    identifier = unicode(_extract_value(vpr_object))
                else:
                    pass
            segment = Segment(start=self._idx[startframe], \
                              end=self._idx[endframe])
            
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
        
    def written(self, value=True, name_alone=False):
        annotation = TrackIDAnnotation(modality=MODALITY_WRITTEN, \
                                       video=self._video)

        for element in self._xmlroot.data.sourcefile.iterchildren():
            # only add PERSONNE objects
            if element.get('name') != 'TEXTE':
                continue

            for vpr_object in element.iterchildren():
                attr_name = vpr_object.get('name')
                if attr_name == 'STARTFRAME':
                    startframe = int(_extract_value(vpr_object))
                elif attr_name == 'ENDFRAME':
                    endframe = int(_extract_value(vpr_object))
                elif attr_name == 'TRANSCRIPTION':
                    identifiers = \
                    _extract_written(unicode(_extract_value(vpr_object)), name_alone=name_alone)
                else:
                    pass
            segment = Segment(start=self._idx[startframe], \
                              end=self._idx[endframe])
            for i, identifier in enumerate(identifiers):
                if identifier not in annotation.IDs or \
                   segment not in annotation(identifier).timeline:
                    name = annotation.auto_track_name(segment, prefix='text')
                    annotation[segment, name, identifier] = value
        
        return annotation
    
    def annotated(self):
        """"""
        timeline = Timeline(video=self._video)
        p = re.compile('([0-9]*):([0-9]*)')
        for element in self._xmlroot.data.sourcefile.iterchildren():
            text = element.get('framespan')
            if text:
                m = p.match(text)
                startframe = int(m.group(1))
                endframe = int(m.group(2))+1
                segment = Segment(start=self._idx[startframe], end=self._idx[endframe])            
                timeline += segment
        
        return timeline        
