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

import numpy as np
from pyannote.algorithm.tagging import ConservativeDirectTagger
from pyannote.base.annotation import Unknown
import sc2llr


class AuthenticationCalibration(object):

    def __init__(self, tagger=None):
        super(AuthenticationCalibration, self).__init__()
        if tagger is None:
            self.tagger = ConservativeDirectTagger()
        else:
            self.tagger = tagger

    def xy(self, reference, scores, labels=None, **kwargs):
        """

        Parameters
        ----------
        reference : `Annotation`

        scores : `Scores`
        labels : list
            List of labels whose scores must be considered.
            In case labels is None (default), use all available labels.

        Returns
        -------
        x,y : (nTracks, nLabels)-shaped numpy arrays
            `nTracks` is the number of tracks in `scores`.
            `nLabels` is the number of labels.
            x[t,l] contains the scores for track #t and label #l.
            y[t,l] contains the groundtruth (i.e. 1 if track #t has label #l,
            0 if it has a different label and -1 if label is not known)
        kw : dict

        """

        if labels is None:
            labels = scores.labels()
            kwargs['labels'] = labels

        nLabels = len(labels)

        # get all tracks (anonymous for now)
        tracks = scores.to_annotation().anonymize_tracks()
        nTracks = len([_ for _ in tracks.itertracks()])

        x = np.zeros((nTracks, nLabels), dtype=float)
        y = np.zeros((nTracks, nLabels), dtype=int)

        # tag tracks than can be tagged
        tagged = self.tagger(reference, tracks)

        for t, (segment, track) in enumerate(tracks.itertracks()):
            label = tagged[segment, track]
            track_scores = scores.get_track_scores(segment, track)
            for l, other_label in enumerate(labels):
                x[t, l] = track_scores[other_label]
                if isinstance(label, Unknown):
                    y[t, l] = -1
                elif label == other_label:
                    y[t, l] = 1
                else:
                    y[t, l] = 0

        return x, y, kwargs

    def train_mapping(self, X, Y, **kwargs):

        # remove NaNs
        ok = np.where(~np.isnan(X))
        x = X[ok]
        y = Y[ok]

        # positive & negative samples
        positive = x[np.where(y == 1)]
        negative = x[np.where(y == 0)]

        #
        s2llr = sc2llr.computeLinearMapping(negative, positive)
        prior = 1. * len(positive) / (len(positive) + len(negative))

        return (s2llr, prior)

    def fit(self, training_data, **kwargs):
        """
        Fit calibration to training data

        Parameters
        ----------
        training_data : list
            List of (annotation, scores) tuples where each tuple is made of
            - groundtruth `annotation` for a given resource
            - identification `scores` for the same resource
        kwargs : dict
            See .xy() method
        """

        X = []
        Y = []

        for data in training_data:
            x, y, kwargs = self.xy(*data, **kwargs)
            X.append(x)
            Y.append(y)

        self.kwargs = kwargs
        self.X = np.vstack(X)
        self.Y = np.vstack(Y)

        self.mapping = self.train_mapping(self.X, self.Y, **(self.kwargs))

        return self

    def apply(self, scores, prior=None):
        """
        Apply score calibration

        Parameters
        ----------
        scores : `Scores`
            Uncalibrated scores.
        prior : float, optional
            When provide, set manual prior p(x|H) to `prior`
            Uses estimated prior by default.

        Returns
        -------
        calibrated : `Scores`
            Calibrated scores

        """

        (a, b), estimated_prior = self.mapping
        if not prior:
            prior = estimated_prior

        def s2p(x):
            # p(x|¬H)/p(x|H)
            lr = 1./np.exp(a*x+b)
            # p(¬H)/p(H)
            rho = (1.-prior)/prior
            return 1./(1.+rho*lr)

        return scores.map(s2p)


if __name__ == "__main__":

    import pickle
    from argparse import ArgumentParser
    import pyannote.cli

    parser = ArgumentParser(description='Calibration of authentication scores')
    subparsers = parser.add_subparsers(help='mode')

    # ==============
    # TRAIN mode
    # ==============

    def trainCalibration(args):
        uris = pyannote.cli.get_uris()
        data = [(args.reference(uri), args.scores(uri)) for uri in uris]
        calibration = AuthenticationCalibration().fit(data)
        with args.output() as f:
            pickle.dump(calibration, f)

    train_parser = subparsers.add_parser('train', help='Train calibration',
                                         parents=[pyannote.cli.parentArgumentParser()])
    train_parser.set_defaults(func=trainCalibration)

    description = 'path to input authentication scores.'
    train_parser.add_argument('scores', help=description,
                              type=pyannote.cli.InputGetAnnotation())

    description = 'path to input reference annotation.'
    train_parser.add_argument('reference', help=description,
                              type=pyannote.cli.InputGetAnnotation())

    description = 'path to output calibration.'
    train_parser.add_argument('output', help=description,
                              type=pyannote.cli.OutputFileHandle())

    # ==============
    # APPLY mode
    # ==============

    def applyCalibration(args):

        uris = pyannote.cli.get_uris()

        with args.calibration() as f:
            calibration = pickle.load(f)

        prior = args.prior if hasattr(args, 'prior') else None

        for u, uri in enumerate(uris):

            if args.verbose:
                sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
                sys.stdout.flush()

            scores = args.scores(uri)
            args.calibrated(calibration.apply(scores, prior=prior))

    apply_parser = subparsers.add_parser('apply', help='Apply calibration',
                                         parents=[pyannote.cli.parentArgumentParser()])
    apply_parser.set_defaults(func=applyCalibration)

    description = 'path to input authentication scores.'
    apply_parser.add_argument('scores', help=description,
                              type=pyannote.cli.InputGetAnnotation())

    description = 'path to input calibration.'
    apply_parser.add_argument('calibration', help=description,
                              type=pyannote.cli.InputFileHandle())

    description = 'path to output calibrated scores.'
    apply_parser.add_argument('calibrated', help=description,
                              type=pyannote.cli.OutputWriteAnnotation())

    description = 'set prior manually (default is to use estimated priors).'
    apply_parser.add_argument('--prior', help=description, type=float,
                              default=pyannote.cli.SUPPRESS)

    # =====================
    # ARGUMENT parsing
    # =====================

    try:
        args = parser.parse_args()
        args.func(args)
    except IOError as e:
        import sys
        sys.stderr.write('%s' % e)
        sys.exit(-1)
