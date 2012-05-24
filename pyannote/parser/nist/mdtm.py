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


from pyannote.base.segment import Segment
from pyannote.parser.base import BaseTextualAnnotationParser

class MDTMParser(BaseTextualAnnotationParser):
    
    def __init__(self):
        multitrack = True
        super(MDTMParser, self).__init__(multitrack)
    
    def _comment(self, line):
        return False
    
    def _parse(self, line):
        
        tokens = line.split()
        # video 1 start duration modality confidence subtype identifier
        
        video = str(tokens[0])
        #channel = tokens[1]
        start_time = float(tokens[2])
        duration = float(tokens[3])
        modality = str(tokens[4])
        #confidence = tokens[5]
        #subtype = tokens[6]
        label = str(tokens[7])

        segment = Segment(start=start_time, end=start_time+duration)
        return segment, None, label, video, modality
    
    def _append(self, annotation, f, video, modality):
        
        if annotation.multitrack:
            format = '%s 1 %%g %%g %s NA %%s %%s\n' % (video, modality)
            for segment, track, label in annotation.iterlabels():
                f.write(format % (segment.start, segment.duration, 
                                  track, label))
        else:
            format = '%s 1 %%g %%g %s NA NA %%s\n' % (video, modality)
            for segment, label in annotation.iterlabels():
                f.write(format % (segment.start, segment.duration, label))
        
if __name__ == "__main__":
    import doctest
    doctest.testmod()
