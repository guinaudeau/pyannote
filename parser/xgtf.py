#!/usr/bin/env python
# encoding: utf-8

from QCompere.base import Segment, TrackIDAnnotation
from idx import IDXParser
from lxml import objectify

MODALITY_HEAD = 'head'
MODALITY_WRITTEN = 'written'

def _extract_value(attr):
    return attr.getchildren()[0].get('value')

def _extract_written(text):
    identifiers = []
    if text:
        elements = unicode(text).split('<pers=')
        for element in elements[1:]:
            identifier = element.split('>')[0]
            identifiers.append(identifier)
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
        
    def written(self, value=True):
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
                    _extract_written(unicode(_extract_value(vpr_object)))
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


class XGTFSample(XGTFParser):
    """docstring for XGTFSample"""
    def __init__(self):
        import os.path
        sample_xgtf = '%s/../data/sample.xgtf' % (os.path.dirname(__file__))
        sample_idx  = '%s/../data/sample.idx'  % (os.path.dirname(__file__))
        super(XGTFSample, self).__init__(sample_xgtf, sample_idx, video='sample')
