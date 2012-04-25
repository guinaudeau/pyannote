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

from pyannote.base.mapping import ManyToOneMapping
from pyannote.base.comatrix import Confusion
from base import BaseMapper

class ArgMaxMapper(BaseMapper):
    """    
    """
    def __init__(self, confusion=None):
        super(ArgMaxMapper, self).__init__()
        if confusion is None:
            self.__confusion = Confusion
        else:
            self.__confusion = confusion
    
    def __get_confusion(self):
        return self.__confusion
    confusion = property(fget=__get_confusion, \
                     fset=None, \
                     fdel=None, \
                     doc="Confusion.")
    
    def associate(self, A, B):
        
        # Confusion matrix
        matrix = self.confusion(A, B)
        
        # ArgMax
        pairs = matrix.argmax(axis=0, threshold=0, ties='any')
        
        # Reverse dict and group alabels by argmax
        sriap = {}
        for a, b_s in pairs.iteritems():
            if b_s:
                b = b_s.pop()
                if b not in sriap:
                    sriap[b] = set([])
                sriap[b].add(a)
        
        M = ManyToOneMapping(A.modality, B.modality)
        
        for b, a_s in sriap.iteritems():
            M += (a_s, [b])                
        alabels, blabels = matrix.labels
        for a in set(alabels)-M.first_set:
            M += ([a], None)
        for b in set(blabels)-M.second_set:
            M += (None, [b])

        return M
        
            
