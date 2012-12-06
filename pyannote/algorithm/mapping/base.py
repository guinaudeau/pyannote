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
    Mapping algorithm base class
    
    Any mapping algorithm must inherit from this base class and implement the 
    ``_associate(A, B)`` method.
    
    """
    
    def _associate(self, A, B):
        """Find the optimal mapping between `A` and `B` labels
        
        BaseMapper sub-classes must implement this method.
        
        Parameters
        ----------
        A, B : :class:`pyannote.base.annotation.Annotation`
        
        Returns
        -------
        mapping : :class:`pyannote.base.mapping.Mapping`
            Mapping between `A` and `B` labels.
        
        """
        raise NotImplementedError("BaseMapper sub-class must implement "
                                  "_associate(A, B) method.")
        
    def __call__(self, A, B, init=None):
        """Find the optimal mapping between `A` and `B` labels
        
        Parameters
        ----------
        A, B : :class:`pyannote.base.annotation.Annotation`
            
        init : :class:`pyannote.base.mapping.Mapping`, optional
            Initial constraint on label mapping. 
        
        Returns
        -------
        mapping : :class:`pyannote.base.mapping.Mapping`
            Optimal mapping between `A` and `B` labels.
        
        Examples
        --------
            
            >>> A = Annotation(modality="left")
            >>> A[Segment(0, 1)] = 'a1'
            >>> A[Segment(1, 2)] = 'a2'
            >>> A[Segment(2, 3)] = 'a3'
            >>> A[Segment(3, 4)] = 'a4'
            
            >>> B = Annotation(modality="right")
            >>> B[Segment(0, 1)] = 'b1'
            >>> B[Segment(1, 2)] = 'b2'
            >>> B[Segment(2, 3)] = 'b3'
            >>> B[Segment(3, 4)] = 'b4'
            
            >>> init = Mapping("left", "right")
            >>> init += (('a1', 'a2'), ('b1', 'b2'))
            >>> init += (('a3', 'a4'), ('b3', 'b4'))
            
            >>> mapper = BaseMapper()
            >>> optimal_mapping = mapper(A, B, init=init)
            
            
        See Also
        --------
        pyannote.base.mapping
        
        """
        
        alabels = set(A.labels())
        blabels = set(B.labels())
        
        # when `init` is not provided
        # mapping has no constraint whatsoever 
        # (any A label can be mapped to any B labels)
        if init is None:
            init = Mapping(A.modality, B.modality)
            init += (alabels, blabels)
        
        # make sure every A and B label is part of at least one sub-mapping
        if not alabels <= init.left_set:
            raise ValueError('Labels %s are missing from initial mapping.' \
                             % alabels - init.left_set)
        if not blabels <= init.right_set:
            raise ValueError('Labels %s are missing from initial mapping.' \
                             % blabels - init.right_set)
        
        # initialize empty mapping between A and B labels
        M = Mapping(A.modality, B.modality)
        
        # process each part of initial mapping separately
        # and concatenate them at the end
        for lblA, lblB in init:
            
            # extract constrained sub-annotations
            # for later mapping between their labels
            a = A.subset(lblA)
            b = B.subset(lblB)
            
            # get actual `a` and `b` labels
            alabels = a.labels()
            blabels = b.labels()
            Na = len(alabels)
            Nb = len(blabels)
            
            # if both `a` and `b` have at least one label
            # find the optimal association and add it to the overal mapping
            if Na > 0 and Nb > 0:
                m = self._associate(a, b)
                M += m
                
            # otherwise, finding the optimal assocation is trivial
            else:
                
                # when there is no `a` labels
                # simply map all `b` labels to nothing.
                if Na < 1:
                    for blabel in blabels:
                        M += (None, [blabel])
                        
                # when there is no `b` labels
                # simply map all `a` labels to nothing.
                if Nb < 1:
                    for alabel in alabels:
                        M += ([alabel], None)
        
        # return the final mapping
        return M

if __name__ == "__main__":
    import doctest
    doctest.testmod()
