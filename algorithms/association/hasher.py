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

from base import BaseAssociation
from pyannote.base.association import Mapping

class IDHasher(BaseAssociation):
    
    def __init__(self, hashA, hashB):
        """
        :param hashA: function that maps identifier to a category (eg the person gender)
        :type hashA: function(identifier) = category
        :param hashB: function that maps identifier to a category (eg the person gender)
        :type hashB: function(identifier) = category
        """
        super(IDHasher, self).__init__()
        self.__hashA = hashA
        self.__hashB = hashB
        
    def associate(self, A, B):
        
        partitionA = {a:self.__hashA(a) for a in A.IDs}
        partitionB = {b:self.__hashB(b) for b in B.IDs}
        
        M = Mapping(A.modality, B.modality)
        
        clusters = set(partitionA.values()) | set(partitionB.values())
        for c in clusters:
            setA = set([a for a in partitionA if partitionA[a] == c])
            setB = set([b for b in partitionB if partitionB[b] == c])
            M += (setA, setB)
        
        return M
        
        
    
        
