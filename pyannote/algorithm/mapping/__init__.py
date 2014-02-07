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

"""

Given two ``Annotation`` objects `A` and `B` of the same audio/video document, label mapping consists in finding the optimal association between `A` labels and `B` labels. 
Depending on the algorithm and the definition of an `optimal` mapping, it can return a one-to-one, many-to-one, one-to-many or many-to-many mapping. 

Several mapping algorithms are available in the ``pyannote.algorithm.mapping`` module.

"""

from hungarian import HungarianMapper
from argmax import ArgMaxMapper, ConservativeDirectMapper

__all__ = ['HungarianMapper', 'ArgMaxMapper', 'ConservativeDirectMapper']

if __name__ == "__main__":
    import doctest
    doctest.testmod()
