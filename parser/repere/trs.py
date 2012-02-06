#!/usr/bin/env python
# encoding: utf-8

from pyannote import Segment, Timeline, TrackIDAnnotation
from lxml import objectify

MODALITY_SPEAKER = 'speaker'
MODALITY_SPOKEN  = 'spoken'

def _extract_spoken(text):
    identifiers = []
    if text:
        elements = unicode(text).split('<pers=')
        for element in elements[1:]:
            identifier = element.split('>')[0]
            #TODO: split Jean-Marie_LEPEN,Marine_LEPEN ("les LEPEN")
            identifiers.append(identifier)
    return identifiers

def _extract_speakers(text):
    identifiers = []
    if text:
        for i, identifier in enumerate(unicode(text).split()):
            identifiers.append(identifier)
    return identifiers

def _fix_incomplete(incomplete, latest_sync):
    for s, segment in enumerate(incomplete):
        segment._end = latest_sync
    return []

class TRSParser(object):
    """
    .trs file parser
    """
    def __init__(self, path2trs, video=None):
        super(TRSParser, self).__init__()
        self._trs = path2trs
        self._xmlroot = objectify.parse(self._trs).getroot()
        self._name = {}
        for speaker in self._xmlroot.Speakers.iterchildren():
            self._name[unicode(speaker.get('id'))] = unicode(speaker.get('name'))
        if video is None:
            self._video = self._xmlroot.get('audio_filename')
        else:
            self._video = video
    
    def transcribed(self, non_transcribed='nontrans'):
        timeline = Timeline(video=self._video)
        for section in self._xmlroot.Episode.iterchildren():
            if section.get('type') != non_transcribed:
                section_start = float(section.get('startTime'))
                section_end   = float(section.get('endTime'))
                segment = Segment(start=section_start, end=section_end)
                timeline += segment
        return timeline
                
    def speaker(self, name=True, value=True):
        annotation = TrackIDAnnotation(modality=MODALITY_SPEAKER, \
                                       video=self._video)
        # parse file looking for speaker info.
        for section in self._xmlroot.Episode.iterchildren():
            for turn in section.iterchildren():
                turn_start = float(turn.get('startTime'))
                turn_end   = float(turn.get('endTime'))
                segment = Segment(start=turn_start, end=turn_end)
                identifiers = _extract_speakers(turn.get('speaker'))
                for i, identifier in enumerate(identifiers):
                    track = annotation.auto_track_name(segment, prefix='speaker')
                    if name:
                        annotation[segment, track, self._name[identifier]] = value
                    else:
                        annotation[segment, track, identifier] = value

        return annotation
    
    def spoken(self, value=True):
        
        annotation = TrackIDAnnotation(modality=MODALITY_SPOKEN, \
                                video=self._video)
        incomplete = []
        
        for section in self._xmlroot.Episode.iterchildren():
            section_start = float(section.get('startTime'))
            section_end   = float(section.get('endTime'))
            
            # ==> SYNC
            latest_sync = section_start
            incomplete = _fix_incomplete(incomplete, latest_sync)
            
            for turn in section.iterchildren():
                turn_start = float(turn.get('startTime'))
                turn_end   = float(turn.get('endTime'))
                
                # ==> SYNC
                latest_sync = turn_start
                incomplete = _fix_incomplete(incomplete, latest_sync)
                
                for element in turn.iterchildren():
                    if element.tag == 'Sync':
                        # ==> SYNC
                        latest_sync = float(element.get('time'))
                        incomplete = _fix_incomplete(incomplete, latest_sync)
                    
                    identifiers = _extract_spoken(element.tail)
                    segment = Segment(start=latest_sync, end=latest_sync+1e-3)
                    incomplete.append(segment)
                    
                    for i, identifier in enumerate(identifiers):
                        track = annotation.auto_track_name(segment, prefix='spoken')
                        annotation[segment, track, identifier] = value
                
                # ==> SYNC
                latest_sync = turn_end
                incomplete = _fix_incomplete(incomplete, latest_sync)
                
            # ==> SYNC
            latest_sync = section_end
            incomplete = _fix_incomplete(incomplete, latest_sync)
        
        return annotation


class TRSSample(TRSParser):
    """docstring for TRSSample"""
    def __init__(self):
        import os.path
        sample_trs = '%s/../data/sample.trs' % (os.path.dirname(__file__))
        super(TRSSample, self).__init__(sample_trs, video='sample')
