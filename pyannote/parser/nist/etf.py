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

from pandas import read_table
from pyannote import Segment
import numpy as np
from pyannote.base.annotation import Scores

class ETF0:
    
    URI = 'uri'
    CHANNEL = 'channel'
    START = 'start'
    DURATION = 'duration'
    MODALITY = 'modality'
    x = 'x'
    LABEL = 'label'
    SCORE = 'value'
    X = 'X'
    
    fields = [URI, CHANNEL, START, DURATION, MODALITY, 'x', LABEL, SCORE, 'X']
    
    SEGMENT = 'segment'


class ETF0Parser(object):
    
    def __init__(self):
        super(ETF0Parser, self).__init__()
    
    def read(self, path, **kwargs):
        
        # load whole file
        df = read_table(path, header=None, sep=' ', names=ETF0.fields)
        
        # add 'segment' column build from start time & duration
        df[ETF0.SEGMENT] = [Segment(s, s+df[ETF0.DURATION][i]) 
                            for i,s in df[ETF0.START].iteritems()]
        
        # obtain list of resources
        uris = list(df[ETF0.URI].unique())
        
        # obtain list of modalities
        modalities = list(df[ETF0.MODALITY].unique())
        
        self.__loaded = {}
        
        # loop on resources
        for uri in uris:
            
            # filter based on resource
            df_ = df[df[ETF0.URI] == uri]
            
            # loop on modalities
            for modality in modalities:
                
                # filter based on modality
                df__ = df_[df_[ETF0.MODALITY] == modality]
                
                s = Scores.from_df(df__, segment=ETF0.SEGMENT, 
                                         track=None,
                                         label=ETF0.LABEL, 
                                         value=ETF0.SCORE,
                                         modality=modality,
                                         uri=uri)
                
                self.__loaded[uri, modality] = s
        
        return self
    
    def __get_uris(self):
        return sorted(set([v for (v, m) in self.__loaded]))
    uris = property(fget=__get_uris)
    """"""
    
    def __get_modalities(self):
        return sorted(set([m for (v, m) in self.__loaded]))
    modalities = property(fget=__get_modalities)
    """"""
    
    def __call__(self, uri=None, modality=None, **kwargs):
        """
        
        Parameters
        ----------
        uri : str, optional
            If None and there is more than one resource 
        modality : str, optional
        
        Returns
        -------
        annotation : :class:`pyannote.base.annotation.Annotation`
        
        """
        
        match = dict(self.__loaded)
        
        # filter out all annotations 
        # but the ones for the requested resource
        if uri is not None:
            match = {(v, m): ann for (v, m), ann in match.iteritems()
                                 if v == uri }
        
        # filter out all remaining annotations 
        # but the ones for the requested modality
        if modality is not None:
            match = {(v, m): ann for (v, m), ann in match.iteritems()
                                 if m == modality}
        
        if len(match) == 0:
            A = DataFrame()
        elif len(match) == 1:
            A = match.values()[0]
        else:
            raise ValueError('Found more than one matching annotation: %s' % match.keys())
        
        return A
    
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()

