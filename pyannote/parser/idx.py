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
IDX file format
"""

import numpy as np
from pyannote.base.segment import Segment
from sklearn.isotonic import IsotonicRegression
from pandas import read_table


class IDXParser(object):

    def __init__(self):
        super(IDXParser, self).__init__()

    def read(self, path):

        # load .idx file using pandas
        df = read_table(
            path, sep='\s+',
            names=['frame_number', 'frame_type', 'bytes', 'seconds']
        )
        x = np.array(df['frame_number'], dtype=np.float)
        y = np.array(df['seconds'], dtype=np.float)

        # train isotonic regression
        self.ir = IsotonicRegression(y_min=np.min(y), y_max=np.max(y))
        self.ir.fit(x, y)

        # store info frame support
        self.xmin = np.min(x)
        self.xmax = np.max(x)

        # store median frame duration
        self.delta = np.median(np.diff(y))

        return self

    def __call__(self, i):
        """Get timestamp"""
        return self.ir.transform([min(self.xmax, max(self.xmin, i))])[0]

    def __getitem__(self, i):
        """Get frame"""
        frame_middle = self(i)
        segment = Segment(start=frame_middle-.5*self.delta,
                          end=frame_middle+.5*self.delta)
        return segment

if __name__ == "__main__":
    import doctest
    doctest.testmod()
