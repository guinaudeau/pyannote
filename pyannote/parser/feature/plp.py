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
from pyannote.base.segment import SlidingWindow
from pyannote.parser.feature.base import BaseBinaryPeriodicFeatureParser

class PLPParser(BaseBinaryPeriodicFeatureParser):
    """
    
    Parameters
    ----------
    sliding_window : :class:`pyannote.base.segment.SlidingWindow`, optional
    
    Notes
    -----
    Read multiple records as one big record.
    
    """
    def __init__(self, sliding_window=None):
        super(PLPParser, self).__init__()
        if sliding_window is None:
            sliding_window = SlidingWindow()
        self.__sliding_window = sliding_window
    
    def _read_header(self, fp):
        """
        Read the header of a .plp file.
        
        Parameters
        ----------
        fp : file
        
        Returns
        -------
        dtype : 
            Feature vector type
        sliding_window : :class:`pyannote.base.segment.SlidingWindow`
            
        count : 
            Number of feature vectors
        
        """
        
        # read number of records
        nrec_type = np.dtype('<i4')
        nrec, = struct.unpack(nrec_type.str, fp.read(nrec_type.itemsize))
        
        # read feature dimension
        dim_type = np.dtype('<i4')
        dim,  = struct.unpack(dim_type.str,  fp.read(dim_type.itemsize))
        
        # read number of features per record
        count_type = np.dtype('<i4')
        count = np.fromfile(fp, dtype=count_type, count=nrec, sep='')
        
        dtype = np.dtype(('<f4', (dim, )))
        count = np.sum(count)
        
        return dtype, self.__sliding_window, count


if __name__ == "__main__":
    import doctest
    doctest.testmod()
