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

import struct
import numpy as np
from pyannote.base.feature import SlidingWindow, \
                                  SlidingWindowFeature, \
                                  TimelineFeature

def _read_bin(path2bin, dimension, base='<f4'):
    
    vec_type = np.dtype((base, (dimension,)))
    
    # open binary file
    f = open(path2bin, 'rb')
    data = np.fromfile(f, dtype=vec_type, sep='')
    f.close()
    
    return data

class BINParser(object):
    """
    Binary file parser
    """
    def __init__(self, path2bin, \
                       dimension, \
                       base='<f4', \
                       video=None):
        super(BINParser, self).__init__()
        self.path2bin = path2bin
        self.dimension = dimension
        self.base = base
        self.video = video
    
    def timeline_feature(self, timeline):
        data = _read_bin(self.path2bin, self.dimension, base=self.base)
        feature = TimelineFeature(data, \
                                  timeline = timeline, \
                                  video=self.video, )
        return feature
    
    def sliding_window_feature(self, sliding_window):
        data = _read_bin(self.path2bin, self.dimension, base=self.base)
        feature = SlidingWindowFeature(data, \
                                       sliding_window = sliding_window, \
                                       video=self.video)
        return feature

if __name__ == "__main__":
    import doctest
    doctest.testmod()

