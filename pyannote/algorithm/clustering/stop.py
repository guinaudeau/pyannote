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

"""This module defines stopping criterion mixin for agglomerative clustering.
"""

class BaseStoppingCriterionMixin(object):
    
    def _stop(self):
        name = self.__class.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  '_stop()' % name)

class NegativeStoppingCriterionMixin(BaseStoppingCriterionMixin):
    
    def _stop(self, value):
        return value < 0.

class MaximumStoppingCriterionMixin(BaseStoppingCriterionMixin):
    
    def _stop(self, value):
        max_value = np.max([v for l, v in self.iterations])
        return value < .9 * max_value

if __name__ == "__main__":
    import doctest
    doctest.testmod()
