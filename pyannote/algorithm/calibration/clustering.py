#!/usr/bin/env python
# encoding: utf-8

# Copyright 2013 Herve BREDIN (bredin@limsi.fr)

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

import itertools
import numpy as np
from pyannote.base.matrix import LabelMatrix
from pyannote.base.annotation import Unknown
from pyannote.stats.llr import LLRLinearRegression, LLRIsotonicRegression


# Helper function for speaker diarization (i.e. speech turns clustering)
def get_groundtruth_from_annotation(annotation):

    # Initialize tracks similarity matrix
    tracks = [(s, t) for (s, t) in annotation.itertracks()]
    G = LabelMatrix(rows=tracks, columns=tracks, dtype=np.float)

    for s, t, label in annotation.itertracks(label=True):

        for s_, t_, other_label in annotation.itertracks(label=True):

            if isinstance(label, Unknown) or isinstance(other_label, Unknown):
                g = np.NaN
            else:
                g = 1 if label == other_label else 0

            G[(s, t), (s_, t_)] = g

    return G


class ClusteringCalibration(object):
    """

    Parameters
    ----------
    method : {'linear', 'isotonic'}, optional
        Default is linear regression of log-likelihood ratio
    equal_priors : boolean, optional
        Defaults to False.
    """

    @classmethod
    def from_file(cls, path):
        import pickle
        with open(path, mode='r') as f:
            calibration = pickle.load(f)
        return calibration

    def to_file(self, path):
        import pickle
        with open(path, mode='w') as f:
            pickle.dump(self, f)

    def __init__(self, method='linear', equal_priors=False):

        super(ClusteringCalibration, self).__init__()

        self.method = method

        if method == 'linear':
            self.llr = LLRLinearRegression()

        elif method == 'isotonic':
            self.llr = LLRIsotonicRegression()

        else:
            raise NotImplementedError(
                'unknown calibration method (%s)' % method)

        self.llr.equal_priors = equal_priors
        self.equal_priors = equal_priors


    def fit(self, matrices, annotations):
        
        X = []
        Y = []

        for m, a in itertools.izip(matrices, annotations):

            for (segment1, track1), (segment2, track2), x in m.itervalues():

                if (segment1, track1) == (segment2, track2):
                    continue

                label1 = a[segment1, track1]
                label2 = a[segment2, track2]

                if isinstance(label1, Unknown) or isinstance(label2, Unknown):
                    y = np.nan
                else:
                    y = np.float(label1 == label2)


                X.append(x)
                Y.append(y)

        self._X = np.array(X)
        self._Y = np.array(Y)

        self.llr.fit(self._X, self._Y)

        return self


    def apply(self, matrix):
        """
        Parameters
        ----------
        matrix : LabelMatrix
            Similarity matrix
        """

        self.llr.equal_priors = self.equal_priors

        return LabelMatrix(
            data=self.llr.toPosteriorProbability(matrix.df.values),
            rows=matrix.get_rows(),
            columns=matrix.get_columns())
