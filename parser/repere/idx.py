#!/usr/bin/env python
# encoding: utf-8

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
    
