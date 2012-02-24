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
from pyannote import SlidingWindow, SlidingWindowFeature

def _read_plp(path2plp):
    
    # open binary file
    f = open(path2plp, 'rb')
    
    # read number of records
    nrec_type = np.dtype('<i4')
    nrec, = struct.unpack(nrec_type.str, f.read(nrec_type.itemsize))
    
    # read feature dimension
    dim_type = np.dtype('<i4')
    dim,  = struct.unpack(dim_type.str,  f.read(dim_type.itemsize))
    
    # read number of features per record
    count_type = np.dtype('<i4')
    count = np.fromfile(f, dtype=count_type, count=nrec, sep='')
    
    
    # read features, for each record
    vec_type = np.dtype(('<f4', (dim, )))
    plp_record = []
    for r in range(nrec):
        plp_record.append(np.fromfile(f, dtype=vec_type, count=count[r], sep=''))
    
    f.close()
    
    return plp_record


class PLPParser(object):
    """
    .plp file parser
    """
    def __init__(self, path2plp, \
                       sliding_window = SlidingWindow(), \
                       video=None):
        super(PLPParser, self).__init__()
        self.path2plp = path2plp
        self.sliding_window = sliding_window
        self.video = video
    
    def feature(self):
        plp_record = _read_plp(self.path2plp)
        data = np.concatenate( [record for record in plp_record], axis=0 )
        feature = SlidingWindowFeature(data, \
                                       sliding_window = self.sliding_window,
                                       video=self.video)
        return feature
        
class PLPSample(PLPParser):
    def __init__(self):
        import os.path
        sample_plp = '%s/../data/sample.12plp' % (os.path.dirname(__file__))
        super(PLPSample, self).__init__(sample_plp, video='sample')
