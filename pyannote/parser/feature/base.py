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
from pyannote.base.feature import PeriodicPrecomputedFeature

class BasePeriodicFeatureParser(object):
    
    def __init__(self):
        super(BasePeriodicFeatureParser, self).__init__()
    
    def _read_header(self, fp):
        """
        Read the header of a binary file.
        
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
        raise NotImplementedError('')
    
    def _read_data(self, fp, dtype, count=-1):
        """
        Construct an array from data in a binary file.
        
        Parameters
        ----------
        file : file
            Open file object
        dtype : data-type
            Data type of the returned array.
            Used to determine the size and byte-order of the items in the file.
        count : int
            Number of items to read. ``-1`` means all items (i.e., the complete
            file).
            
        Returns
        -------
        
        """
        raise NotImplementedError('')
        
    def read(self, path, video=None):
        """
        
        Parameters
        ----------
        path : str
            path to binary feature file
        video : str, optional
        
        Returns
        -------
        feature : :class:`pyannote.base.feature.PeriodicPrecomputedFeature`
            
        
        """
        
        # open binary file
        fp = open(path, 'rb')
        # read header
        dtype, sliding_window, count = self._read_header(fp)
        # read data
        data = self._read_data(fp, dtype, count=count)
        
        # if `video` is not provided, use `path` instead
        if video is None:
            video = str(path)
        
        # create feature object
        feature =  PeriodicPrecomputedFeature(data, sliding_window, 
                                              video=video)
        # close binary file
        fp.close()
        
        return feature

class BaseBinaryPeriodicFeatureParser(BasePeriodicFeatureParser):
    
    """
    Base class for periodic feature stored in binary format.
    """
    
    def __init__(self):
        super(BaseBinaryPeriodicFeatureParser, self).__init__()
        
    def _read_data(self, fp, dtype, count=-1):
        """
        Construct an array from data in a binary file.
        
        Parameters
        ----------
        file : file
            Open file object
        dtype : data-type
            Data type of the returned array.
            Used to determine the size and byte-order of the items in the file.
        count : int
            Number of items to read. ``-1`` means all items (i.e., the complete
            file).
            
        Returns
        -------
        
        """
        return np.fromfile(fp, dtype=dtype, sep='', count=count)

class BaseTextualPeriodicFeatureParser(BasePeriodicFeatureParser):
    
    def __init__(self):
        super(BaseTextualPeriodicFeatureParser, self).__init__()
    
    def _read_data(self, fp, dtype, count=-1):
        raise NotImplementedError('')


if __name__ == "__main__":
    import doctest
    doctest.testmod()
