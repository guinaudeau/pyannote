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


"""This module defines stopping criterion mixins (SMx) for agglomerative clustering.
"""

__all__ = ['LessThanSMx', 'MoreThanSMx', 'NegativeSMx', 
           'NumberOfClustersSMx', 
           'MaximumModularitySMx']

from base import LessThanSMx, MoreThanSMx, NegativeSMx
from structure import NumberOfClustersSMx
from graph import MaximumModularitySMx

if __name__ == "__main__":
    import doctest
    doctest.testmod()
