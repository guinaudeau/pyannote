#!/usr/bin/env python
# encoding: utf-8

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
        
        
    
        
