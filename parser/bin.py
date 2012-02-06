#!/usr/bin/env python
# encoding: utf-8

import struct
import numpy as np
from pyannote import SlidingWindow, SlidingWindowFeature, TimelineFeature

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
    
