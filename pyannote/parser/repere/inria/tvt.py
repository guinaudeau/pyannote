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

import pandas
from pyannote.base.matrix import LabelMatrix

def get_number(head_number):
    return head_number.split('_')[1]
    
class TVTParser(object):
    def __init__(self):
        super(TVTParser, self).__init__()
    
    def read(self, path):
        names = ['u', 'start', 'duration', 't1', 't2', 'distance']
        converters = {'t1': get_number, 't2': get_number}
        data = pandas.read_table(path, sep='[\t ]+', header=None, 
                                 names=names, converters=converters)
        matrix = pandas.pivot_table(data, values='distance', 
                                    rows=['t1'], cols=['t2'])
        ilabels = list(matrix.index)
        jlabels = list(matrix.columns)
        M = matrix.values
        return LabelMatrix(ilabels=ilabels, jlabels=jlabels, Mij=M)