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
from pyannote.parser.base import BaseTextualTimelineParser

class UEMParser(BaseTextualTimelineParser):
    
    def __init__(self):
        super(UEMParser, self).__init__()
    
    def _comment(self, line):
        return line[:2] == ';;'
    
    def _parse(self, line):
        
        tokens = line.split()
        # video channel start end
        
        video = str(tokens[0])
        #channel = tokens[1]
        start_time = float(tokens[2])
        end_time = float(tokens[3])
        segment = Segment(start=start_time, end=end_time)
        
        return segment, video

if __name__ == "__main__":
    import doctest
    doctest.testmod()
