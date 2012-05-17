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

import numpy as np
from pyannote.base.segment import Segment

class IDXParser(object):
    
    def __init__(self):
        super(IDXParser, self).__init__()
    
    def read(self, path):
        
        # frame number to timestamp conversion
        self.__time = {}
        
        # open .idx file
        f = open(path, 'r')
        for line in f:
            # 13 P     125911    0.384
            # idx type byte seconds
            fields = line.strip().split()
            idx = int(fields[0])
            # type = fields[1]
            # byte = int(fields[2])
            seconds = float(fields[3])
            self.__time[idx] = seconds
            
        # close .idx file
        f.close()
        
        # fix it.
        # average delta between two consecutive frames
        m = min(self.__time)
        M = max(self.__time)
        deltas = [self.__time[idx]-self.__time[idx-1] 
                  for idx in range(m+1, M)
                  if idx in self.__time and (idx-1) in self.__time]
        self.__delta = float(np.median(deltas))
        for idx in range(m, M):
            if idx not in self.__time:
                self.__time[idx] = self.__time[idx-1] + self.__delta
        
        return self
    
    def __call__(self, i):
        """Get timestamp"""
        return self.__time[i]
    
    def __getitem__(self, i):
        """Get frame"""
        frame_middle = self.__time[i]
        segment = Segment(start=frame_middle-.5*self.__delta,
                          end=frame_middle+.5*self.__delta)
        return segment

if __name__ == "__main__":
    import doctest
    doctest.testmod()

