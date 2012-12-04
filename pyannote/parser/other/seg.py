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
        super(SEGParser, self).__init__()
        if sliding_window is None:
            sliding_window = SlidingWindow()
        self.__sliding_window = sliding_window
    
    def _comment(self, line):
        return line[0] == '#'
    
    def _parse(self, line):
        
        tokens = line.split()
        # uri label 1 start duration
        
        uri = str(tokens[0])
        label = str(tokens[1])
        #channel = tokens[2]
        i0 = int(tokens[3])
        n = int(tokens[4])
        segment = self.__sliding_window.rangeToSegment(i0, n)
        return segment, None, label, uri, None

if __name__ == "__main__":
    import doctest
    doctest.testmod()
