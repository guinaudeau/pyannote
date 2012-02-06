#!/usr/bin/env python
# encoding: utf-8

from pyannote import IDAnnotation, Segment, SlidingWindow

class SEGParser(object):
    """
    .seg file parser
    """
    def __init__(self, path2seg, \
                       video=None, \
                       modality=None, \
                       sliding_window=SlidingWindow(), \
                       ):
        
        super(SEGParser, self).__init__()
        self.path2seg = path2seg
        
        # read video name from .seg file if needed
        if video is None:
            # find video in .seg file
            # (first field of first uncommented line)
            f = open(self.path2seg, 'r')
            for line in f:
                # skip commented line
                if line[0] == '#':
                    continue
                self.video = line.split()[0]
                break
        else:
            self.video = video
        
        # store modality
        self.modality = modality
        
        # if sliding_window is provided, store it for later use
        # otherwise, assumes .seg files contains timestamps and duration in seconds
        # (rather than frame id and number)
        self.sliding_window = sliding_window
        
        # empty annotation
        self.seg = IDAnnotation(modality=self.modality, video=self.video)
        
        # parse file
        f = open(self.path2seg, 'r')
        for line in f:
            # skip comments
            if line[0] == '#':
                continue
            # split line into fields
            fields = line.split()
            # _video = fields[0]
            identifier = fields[1]
            # _sentence = fields[2]
            raw_i = fields[3]
            raw_n = fields[4]
            
            # compute Segment
            if self.sliding_window is not None:
                segment = self.sliding_window.toSegment(int(raw_i) - 1, int(raw_n))
            else:
                segment = Segment(float(raw_i), float(raw_i) + float(raw_n))
            
            self.seg[segment, identifier] = {'confidence': 1.}
            #self.seg.add(segment, identifier, attributes={}, confidence=1.)
    
    def annotation(self):
        return self.seg
        
    def timeline(self):
        return self.seg.timeline

class SEGSample(SEGParser):
    def __init__(self):
        import os.path
        sample_seg = '%s/../data/sample.1.seg' % (os.path.dirname(__file__))
        super(SEGSample, self).__init__(sample_seg, video='sample')

def toSEG(annotation, toFrameRange, delta=0, order_by='time'):
    """
    
    order_by: 'time' or 'id'
    """
    modality = annotation.modality
    video    = annotation.video
    text = ''
    
    if order_by == 'time':
        for s, segment in enumerate(annotation):
            i0, n = toFrameRange(segment)
            for i, identifier in enumerate(annotation.identifiers(segment=segment)):
                # source id 1 start duration
                text += '%s %s 1 %d %d\n' % (video, identifier, i0+delta, n)
    elif order_by == 'id':
        identifiers = annotation.identifiers()
        for i, identifier in enumerate(identifiers):
            segments = annotation[identifier]
            for segment in segments:
                i0, n = toFrameRange(segment)
                text += '%s %s 1 %d %d\n' % (video, identifier, i0+delta, n)
    else:
        raise ValueError('Unknow order_by argument -- must be time or id')
    
    return text
