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

The ``pyannote.algorithm.mapping`` module contains the various mapping algorithms available in ``PyAnnote``.

Mapping consists in finding the optimal association between labels from two different annotations. 

The output of such algorithms can be one-to-one, many-to-one, one-to-many or many-to-many label mapping.

"""

from hungarian import HungarianMapper
from argmax import ArgMaxMapper

__all__ = ['HungarianMapper', 'ArgMaxMapper']

if __name__ == "__main__":
    import doctest
    doctest.testmod()
