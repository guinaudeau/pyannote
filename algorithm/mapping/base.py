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

from pyannote.base.mapping import Mapping

class BaseMapper(object):
    """
    Every mapping algorithm must inherit from this class and implement
    the .associate(A, B) method.
    """
    
    def associate(self, A, B):
        """Must be implemented by subclass"""
        raise NotImplementedError('')
        
    def __call__(self, A, B, init=None):
        """
        Returns A <--> B mapping 
        """
        if init is None:
            init = Mapping(A.modality, B.modality)
            init += (A.labels(), B.labels())
        
        M = Mapping(A.modality, B.modality)
        
        # process each part of initial mapping separately
        # and concatenate them at the end
        for lblA, lblB in init:   
            a = A(lblA)            
            b = B(lblB)
            
            alabels = a.labels()
            blabels = b.labels()
            Na = len(alabels)
            Nb = len(blabels)
            
            if Na > 0 and Nb > 0:
                m = self.associate(a, b)            
                M += m
            else:
                if Na < 1:
                    for blabel in blabels:
                        M += (None, [blabel])
                if Nb < 1:
                    for alabel in alabels:
                        M += ([alabel], None)
        return M

if __name__ == "__main__":
    import doctest
    doctest.testmod()
