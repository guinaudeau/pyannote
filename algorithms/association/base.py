#!/usr/bin/env python
# encoding: utf-8

from pyannote.base.association import Mapping

class BaseAssociation(object):

    def associate(self, A, B):
        raise NotImplementedError('')
        
    def __call__(self, A, B, init=None):
        
        if init is None:
            init = Mapping(A.modality, B.modality)
            init += (A.IDs, B.IDs)
        
        M = Mapping(A.modality, B.modality)
        
        # process each part of initial mapping separately
        # and concatenate them at the end
        for lblA, lblB in init:
            
            a = A(lblA)            
            b = B(lblB)
            m = self.associate(a, b)            
            M += m
        
        return M
    