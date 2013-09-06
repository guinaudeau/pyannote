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
from pyannote.stats.likelihood_ratio import LogLikelihoodRatioLinearRegression


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
    method : {'LinReg'}, optional
        Default is linear regression of log-likelihood ratio
    """

    def __init__(self, method=None, **kwargs):
        super(ClusteringCalibration, self).__init__()

        if method is None:
            self.method = 'LinReg'

        if self.method == 'LinReg':
            self.calibration = LogLikelihoodRatioLinearRegression(**kwargs)

    def get_training_data(self, groundtruth_iterator, similarity_iterator):
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

    def fit(self, groundtruth_iterator, similarity_iterator, **kwargs):
        """

        Parameters
        ----------
        groundtruth_iterator, similarity_iterator : `LabelMatrix` iterators

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

        x, y = self.get_training_data(
            groundtruth_iterator, similarity_iterator
        )

        ok = np.where(~np.isnan(x))
        x = x[ok]
        y = y[ok]

        positive = x[np.where(y == 1)]
        negative = x[np.where(y == 0)]

        self.calibration.fit(positive, negative, **kwargs)

        return self

    def apply(self, similarity, **kwargs):
        """
        Parameters
        ----------
        similarity : LabelMatrix
            Similarity matrix
        """
        return LabelMatrix(
            data=self.calibration.toPosteriorProbability(
                similarity.df.values, **kwargs
            ),
            rows=similarity.get_rows(),
            columns=similarity.get_columns())


# if __name__ == "__main__":

#     import pickle
#     import sys
#     from argparse import ArgumentParser
#     import pyannote.cli

#     parser = ArgumentParser(description='Calibration of clustering metrics')
#     subparsers = parser.add_subparsers(help='mode')

#     # ==============
#     # TRAIN mode
#     # ==============

#     def trainCalibration(args):
#         uris = pyannote.cli.get_uris()
#         if not uris:
#             raise IOError('Empty list of resources. Please use --uris option.')

#         def _get_tracks(uri):
#             tracks = args.tracks(uri)
#             if hasattr(args, 'uem'):
#                 uem = args.uem(uri)
#                 tracks = tracks.crop(uem, mode='loose')
#             return tracks

#         if hasattr(args, 'reference'):
#             data = [
#                 (args.reference(uri), _get_tracks(uri), args.similarity(uri))
#                 for uri in uris
#             ]
#         else:
#             data = [
#                 (None, _get_tracks(uri), args.similarity(uri))
#                 for uri in uris
#             ]
#         calibration = ClusteringCalibration().fit(data)
#         with args.output() as f:
#             pickle.dump(calibration, f)

#     train_parser = subparsers.add_parser(
#         'train', help='Train calibration',
#         parents=[pyannote.cli.parentArgumentParser()]
#     )

#     train_parser.set_defaults(func=trainCalibration)

#     description = 'path to input similarity metric matrices.'
#     train_parser.add_argument(
#         'similarity', help=description,
#         type=pyannote.cli.InputGetMatrix()
#     )

#     description = 'path to input tracks.'
#     initArgs = {'load_ids': True}
#     train_parser.add_argument(
#         'tracks', help=description,
#         type=pyannote.cli.InputGetAnnotation(initArgs=initArgs)
#     )

#     description = 'path to output calibration.'
#     train_parser.add_argument(
#         'output', help=description,
#         type=pyannote.cli.OutputFileHandle()
#     )

#     description = 'path to input reference annotation.'
#     train_parser.add_argument(
#         '--reference', help=description,
#         default=pyannote.cli.SUPPRESS,
#         type=pyannote.cli.InputGetAnnotation()
#     )

#     # ==============
#     # APPLY mode
#     # ==============
#     def applyCalibration(args):
#         uris = pyannote.cli.get_uris()
#         if not uris:
#             raise IOError('Empty list of resources. Please use --uris option.')

#         with args.calibration() as f:
#             calibration = pickle.load(f)

#         prior = args.prior if hasattr(args, 'prior') else None

#         for uri in uris:

#             similarity = args.similarity(uri)

#             calibrated = calibration.apply(similarity, prior=prior)
#             with args.calibrated(uri=uri) as f:
#                 pickle.dump(calibrated, f)

#     apply_parser = subparsers.add_parser(
#         'apply', help='Apply calibration',
#         parents=[pyannote.cli.parentArgumentParser()]
#     )
#     apply_parser.set_defaults(func=applyCalibration)

#     description = 'path to input similarity metric matrices.'
#     apply_parser.add_argument(
#         'similarity', help=description,
#         type=pyannote.cli.InputGetMatrix()
#     )

#     description = 'optional path to input tracks.'
#     apply_parser.add_argument(
#         '--tracks', help=description,
#         default=pyannote.cli.SUPPRESS,
#         type=pyannote.cli.InputGetAnnotation()
#     )

#     description = 'path to input calibration.'
#     apply_parser.add_argument(
#         'calibration', help=description,
#         type=pyannote.cli.InputFileHandle()
#     )

#     description = 'path to output calibrated similarity metric matrices.'
#     apply_parser.add_argument(
#         'calibrated', help=description,
#         type=pyannote.cli.OutputFileHandle()
#     )

#     description = 'set prior manually (default is to use estimated priors).'
#     apply_parser.add_argument(
#         '--prior', help=description, type=float,
#         default=pyannote.cli.SUPPRESS
#     )

#     # =====================
#     # ARGUMENT parsing
#     # =====================

#     try:
#         args = parser.parse_args()
#         args.func(args)
#     except IOError as e:
#         sys.stderr.write('%s' % e)
#         sys.exit(-1)
