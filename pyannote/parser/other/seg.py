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

from pyannote.base.segment import SlidingWindow
from pyannote.parser.base import BaseTextualAnnotationParser

class SEGParser(BaseTextualAnnotationParser):
    
    def __init__(self, sliding_window=None):
        multitrack = False
        super(SEGParser, self).__init__(multitrack)
        if sliding_window is None:
            sliding_window = SlidingWindow()
        self.__sliding_window = sliding_window
    
    def _comment(self, line):
        return line[0] == '#'
    
    def _parse(self, line):
        
        tokens = line.split()
        # video label 1 start duration
        
        video = str(tokens[0])
        label = str(tokens[1])
        #channel = tokens[2]
        i0 = int(tokens[3])
        n = int(tokens[4])
        segment = self.__sliding_window.rangeToSegment(i0, n)
        return segment, None, label, video, None


# 
# class SEGParser(GenericParser):
#     """
#     .seg file parser
#     """
#     def __init__(self, path2seg, \
#                        modality=None, \
#                        multitrack=False, \
#                        sliding_window=SlidingWindow()):
#         
#         # source identifier 1 start duration
#         format = '{VIDEO} {ID} {NA} {START} {DURATION}' 
#         super(SEGParser, self).__init__(path2seg, \
#                                          format, \
#                                          modality=modality, \
#                                          sliding_window = sliding_window, \
#                                          multitrack = multitrack)

# def toSEG(annotation, toFrameRange, delta=0, order_by='time'):
#     """
#     
#     order_by: 'time' or 'id'
#     """
#     modality = annotation.modality
#     video    = annotation.video
#     text = ''
#     
#     if order_by == 'time':
#         for s, segment in enumerate(annotation):
#             i0, n = toFrameRange(segment)
#             for i, identifier in enumerate(annotation.identifiers(segment=segment)):
#                 # source id 1 start duration
#                 text += '%s %s 1 %d %d\n' % (video, identifier, i0+delta, n)
#     elif order_by == 'id':
#         identifiers = annotation.identifiers()
#         for i, identifier in enumerate(identifiers):
#             segments = annotation[identifier]
#             for segment in segments:
#                 i0, n = toFrameRange(segment)
#                 text += '%s %s 1 %d %d\n' % (video, identifier, i0+delta, n)
#     else:
#         raise ValueError('Unknow order_by argument -- must be time or id')
#     
#     return text

if __name__ == "__main__":
    import doctest
    doctest.testmod()
