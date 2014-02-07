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

import scipy.io
from pyannote.base.matrix import LabelMatrix


class METRICMATParser(object):

    def __init__(self, aggregation='average', **kwargs):
        super(METRICMATParser, self).__init__()
        if aggregation == 'average':
            self.aggregation = 0
        elif aggregation == 'minimum':
            self.aggregation = 1
        else:
            raise ValueError("aggregation must be 'average' or 'minimum'")

    def read(self, path, **kwargs):
        """

        Parameters
        ----------
        path : str
            Path to metric.mat file

        Returns
        -------
        matrix : LabelMatrix

        """

        mat = scipy.io.loadmat(path)

        # list of tracks
        tracks = [str(idx) for idx in mat['tracker_idx'][0, :]]

        # top-right triangle of distance matrix
        D = mat['track_distances'][:, :, self.aggregation]
        # make it symmetric
        D = D + D.T
        for i in range(D.shape[0]):
            D[i, i] = .5*D[i, i]

        return LabelMatrix(ilabels=tracks, jlabels=tracks, Mij=D)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
