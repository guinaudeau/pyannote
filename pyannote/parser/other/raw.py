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
from pyannote.base.segment import SlidingWindow
from pyannote.parser.base import BaseBinaryPeriodicFeatureParser

class RawBinaryPeriodicFeatureParser(BaseBinaryPeriodicFeatureParser):
    
    def __init__(self, dimension=1, base_type='<f4', sliding_window=None):
        super(RawBinary, self).__init__()
        self.__dtype = np.dtype((base_type, (dimension, )))
        if sliding_window is None:
            sliding_window = SlidingWindow()
        self.__sliding_window = sliding_window
    
    def _read_header(self, fp):
        return self.__dtype, self.__sliding_window, -1
        

if __name__ == "__main__":
    import doctest
    doctest.testmod()
