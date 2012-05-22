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

"""This module defines constraint mixin for agglomerative clustering.

    A *ConstraintMixin must implement the following methods:
        * _initialize_constraint()
        * _update_constraint(new_label, old_labels)
        * _mergeable(labels)

"""


class BaseConstraintMixin(object):
    
    def _initialize_constraint(self):
        name = self.__class.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  '_initialize_constraint()' % name)
    def _update_constraint(self, new_label, merged_labels):
        name = self.__class.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  '_update_constraint()' % name)
    def _mergeable(self, labels):
        name = self.__class.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  '_mergeable()' % name)

from pyannote.base.matrix import LabelMatrix
class ContiguousConstraintMixin(BaseConstraintMixin):
    """
    Two labels are mergeable if they are contiguous
    """
    
    def __get_tolerance(self):
        return self.__tolerance
    def __set_tolerance(self, value):
        self.__tolerance = float(value)
    tolerance = property(fget=__get_tolerance, fset=__set_tolerance)
    
    def _xsegment(self, segment):
        """
        Extend segment by half tolerance on both side
        """
        return .5*self.tolerance << segment >> .5*self.tolerance
    
    def _initialize_constraint(self):
        """
        Two labels are mergeable if they are contiguous
        """
        
        self._mergeable = LabelMatrix(default=0.)
        labels = self.annotation.labels()
        for l, label in enumerate(labels):
            
            # extended coverage
            cov = self.annotation(label).timeline.coverage()
            xcov = cov.copy(segment_func=self._xsegment)
            
            for other_label in labels[l+1:]:
                
                # other extended coverage
                other_cov = self.annotation(other_label).timeline.coverage()
                other_xcov = other_cov.copy(segment_func=self._xsegment)
                
                # are labels contiguous?
                if xcov & other_xcov:
                    self._mergeable[label, other_label] = 1.
                    self._mergeable[other_label, label] = 1.
                else:
                    self._mergeable[label, other_label] = 0.
                    self._mergeable[other_label, label] = 0.
    
    def _update_constraint(self, new_label, merged_labels):
        
        # remove rows and columns for old labels
        for label in merged_labels:
            if label == new_label:
                continue
            del self._mergeable[label, :]
            del self._mergeable[:, label]
        
        # extended coverage
        cov = self.annotation(new_label).timeline.coverage()
        xcov = cov.copy(segment_func=self._xsegment)
        
        # update row and column for new label
        labels = self.annotation.labels()
        
        for label in labels:
            
            if label == new_label:
                continue
                
            # other extended coverage
            other_cov = self.annotation(label).timeline.coverage()
            other_xcov = other_cov.copy(segment_func=self._xsegment)
                
            # are labels contiguous?
            if xcov & other_xcov:
                self._mergeable[new_label, label] = 1.
                self._mergeable[label, new_label] = 1.
            else:
                self._mergeable[new_label, label] = 0.
                self._mergeable[label, new_label] = 0.
    
    def _mergeable(self, labels):
        for l, label in enumerate(labels):
            for other_label in labels[l+1, :]:
                if self._mergeable[label, other_label] == 0.:
                    return False
        return True

if __name__ == "__main__":
    import doctest
    doctest.testmod()
