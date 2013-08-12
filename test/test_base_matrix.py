#!/usr/bin/env python
# encoding: utf-8

# Copyright 2012-2013 Herve BREDIN (bredin@limsi.fr)

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


import numpy as np
from pyannote import LabelMatrix


class test_base_matrix(object):

    def setup(self):
        rows = [1, 2, 3]
        columns = ['A', 'B', 'C', 'D']
        data = np.array(
            [
                [1, 4, 3, 2],
                [2, 3, 1, 4],
                [3, 1, 4, 3]
            ]
        )
        self.m = LabelMatrix(
            data=data, dtype=np.float,
            index=rows, columns=columns
        )

    def teardown(self):
        pass

    def test_shape(self):
        assert self.m.shape == (3, 4)

    def test_get_rows(self):
        assert self.m.get_rows() == [1, 2, 3]

    def test_get_columns(self):
        assert self.m.get_columns() == ['A', 'B', 'C', 'D']

    def test_getitem(self):
        assert self.m[2, 'C'] == 1

    def test_setitem(self):
        copied = self.m.copy()
        copied[1, 'D'] = 10
        print copied
        assert copied[1, 'D'] == 10

    def test_iter_values(self):
        V = set([(r, c, v) for (r, c, v) in self.m.iter_values()])
        W = set([
            (1, 'A', 1), (1, 'B', 4), (1, 'C', 3), (1, 'D', 2),
            (2, 'A', 2), (2, 'B', 3), (2, 'C', 1), (2, 'D', 4),
            (3, 'A', 3), (3, 'B', 1), (3, 'C', 4), (3, 'D', 3),
        ])
        assert V == W

    def test_neg(self):
        negated = -self.m
        assert negated.loc[2, 'C'] == -1

    def test_argmin(self):
        assert self.m.argmin(axis=0) == {'A': 1, 'B': 3, 'C': 2, 'D': 1}
        assert self.m.argmin(axis=1) == {1: 'A', 2: 'C', 3: 'B'}
        assert self.m.argmin(axis=None) in [{1: 'A'}, {2: 'C'}, {3: 'B'}]

    def test_argmax(self):
        assert self.m.argmax(axis=0) == {'A': 3, 'B': 1, 'C': 3, 'D': 2}
        assert self.m.argmax(axis=1) == {1: 'B', 2: 'D', 3: 'C'}
        assert self.m.argmax(axis=None) in [{1: 'B'}, {2: 'D'}, {3: 'C'}]

    def test_copy(self):
        copied = self.m.copy()
        assert copied.loc[2, 'C'] == 1
