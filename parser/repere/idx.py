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

class IDXParser(object):
    
    def __init__(self, path2idx):
        
        super(IDXParser, self).__init__()
        self.path2idx = path2idx
        
        self.__time = {}
        f = open(self.path2idx, 'r')
        for line in f:
            # sample line:
            # 13 P     125911    0.384
            # f0 f1    f2        f3
            fields = line.split()
            idx = int(fields[0])
            sec = float(fields[3])
            self.__time[idx] = sec
        f.close()
        
        # fix it.
        # average delta between two consecutive frames
        m = min(self.__time)
        M = max(self.__time)
        self.__delta = np.median([self.__time[idx]-self.__time[idx-1] \
                                  for idx in range(m+1, M) \
                                  if idx in self.__time and (idx-1) in self.__time])
        
        count = 0
        for idx in range(m, M):
            if idx not in self.__time:
                self.__time[idx] = self.__time[idx-1] + self.__delta
    
    def __get_delta(self): 
        return self.__delta
    delta = property(fget=__get_delta, \
                     fset=None, \
                     fdel=None, \
                     doc="Median frame duration.")
    
    
    
    def __call__(self, idx):
        return self.__time[idx]
    
