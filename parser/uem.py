#!/usr/bin/env python
# encoding: utf-8

from ..base import Segment, Timeline

class UEMParser(object):
    """
    .uem file parser
    """
    def __init__(self, path2uem, \
                       ):
        
        super(UEMParser, self).__init__()
        self.path2uem = path2uem
        
        # empty list of uems
        self.uems = {}
        
        # parse file
        f = open(self.path2uem, 'r')
        for line in f:
            # skip comments
            if line[:2] == ';;':
                continue
            # split line into fields
            fields = line.strip().split()
            video = fields[0]
            channel = int(fields[1])
            start = float(fields[2])
            end   = float(fields[3])
            
            if video not in self.uems:
                self.uems[video] = Timeline(video=video)
            
            self.uems[video] += Segment(start, end)
    
    def timeline(self, video):
        return self.uems[video]
    
    def videos(self):
        return self.uems.keys()
    
def toUEM(timeline):
    """"""
    video = timeline.video
    text = ''
    for s, segment in enumerate(timeline):
        start = segment.start
        end = segment.end
        text += '%s 1 %g %g\n' % (video, start, end)
    return text

