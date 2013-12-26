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

        self.equal_priors = equal_priors

    def _get_training_data(self, groundtruth_iterator, similarity_iterator):
        """

        Parameters
        ----------
        groundtruth_iterator, similarity_iterator : `LabelMatrix` iterators

        Returns
        -------
        x, y : numpy array

        Notes
        -----
        `groundtruth_iterator` should yield G matrices such that for each row r
        and each column c, G[r, c] = {0, 1, np.NaN}:
         - '1' indicates that elements r and c are in the same cluster
           according to the groundtruth.
         - '0' indicates that they are in two different clusters.
         - 'np.NaN' is used when no information is available

        `similarity_iterator` should yield S matrices with same rows and
        columns as G matrices, such that S[r, c] provides a number describing
        how similar (or dissimilar) elements r and c are to each other.
        Use np.NaN in case similarity is not available.

        """
        x = []
        y = []

        for groundtruth, similarity in itertools.izip(
            groundtruth_iterator, similarity_iterator
        ):

            for row, column, gt in groundtruth.itervalues():
                sim = similarity[row, column]

                # skip self similarity
                if row == column:
                    continue

                x.append(sim)
                y.append(gt)

        x = np.array(x)
        y = np.array(y)

        return x, y

    def fit(self, groundtruth, similarity, **kwargs):
        """

        Parameters
        ----------
        groundtruth, similarity : `LabelMatrix` iterators

        Notes
        -----
        `groundtruth` should yield G matrices such that for each row r
        and each column c, G[r, c] = {0, 1, np.NaN}:
         - '1' indicates that elements r and c are in the same cluster
           according to the groundtruth.
         - '0' indicates that they are in two different clusters.
         - 'np.NaN' is used when no information is available

        `similarity` should yield S matrices with same rows and
        columns as G matrices, such that S[r, c] provides a number describing
        how similar (or dissimilar) elements r and c are to each other.
        Use np.NaN in case similarity is not available.

        """

        x, y = self._get_training_data(groundtruth, similarity)

        ok = np.where(~np.isnan(x))
        x = x[ok]
        y = y[ok]

        self.llr.fit(x, y)

        return self

    def apply(self, similarity):
        """
        Parameters
        ----------
        similarity : LabelMatrix
            Similarity matrix
        """

        if self.equal_priors:
            prior = 0.5
        else:
            prior = None

        return LabelMatrix(
            data=self.llr.toPosteriorProbability(
                similarity.df.values, prior=prior
            ),
            rows=similarity.get_rows(),
            columns=similarity.get_columns())
