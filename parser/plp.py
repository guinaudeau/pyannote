#!/usr/bin/env python
# encoding: utf-8

import struct
import numpy as np
from QCompere.base.feature import SlidingWindow, SlidingWindowFeature

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
