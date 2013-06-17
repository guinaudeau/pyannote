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
from pyannote.base.annotation import Unknown
from pyannote.base.matrix import LabelMatrix
import sc2llr
import pandas
from scipy.spatial.distance import squareform


class ClusteringCalibration(object):

    def __init__(self, tagger=None):
        super(ClusteringCalibration, self).__init__()
        if tagger is None:
            import pyannote.algorithm.tagging
            self.tagger = pyannote.algorithm.tagging.ConservativeDirectTagger()
        else:
            self.tagger = tagger

    def xy(self, reference, tracks, similarity, **kwargs):
        """

        Parameters
        ----------
        tracks : `Annotation`
            Hypothesis segmentation
        similarity : `pandas.DataFrame`
            Similarity between tracks.
        reference : `Annotation`
            Groundtruth annotation used to tag `tracks`
            In case `reference` is None, we suppose `tracks` are already tagged

        Returns
        -------
        x,y : (nTracks, nTracks)-shaped numpy arrays
            `nTracks` is the number of tracks in `tracks`.
            x[t1,t2] contains the similarity of tracks #t1 #t2
            y[t1,t2] contains the groundtruth (i.e. 1 if tracks #t1 and #t2
            share the same label, 0 if they have two different labels
            and -1 if it is unsure.
        kw : dict

        """

        if isinstance(similarity, LabelMatrix):
            similarity = labelMatrix_to_dataFrame(similarity, tracks)

        # get number of tracks
        allTracks = [(s, t) for s, t in tracks.itertracks()]
        nTracks = len(allTracks)

        # tag tracks than can be tagged
        if reference:
            tagged = self.tagger(reference, tracks.anonymize_tracks())
        else:
            tagged = tracks

        # y contains
        y = np.zeros((nTracks, nTracks), dtype=int)
        for t, (segment, track) in enumerate(allTracks):
            label = tagged[segment, track]

            # if track is unknown, fill the corresponding line and row with -1
            # and go to next track
            if isinstance(label, Unknown):
                y[t, :] = -1
                y[:, t] = -1
                y[t, t] = 1
                continue

            for T, (other_segment, other_track) in enumerate(allTracks):
                # if we reached the diagonal of the matrix
                # go to next track
                if t == T:
                    y[t, t] = 1
                    break

                other_label = tagged[other_segment, other_track]

                # if other_track is unknown, it was already taken care of
                # in the outter loop, so go to next other track
                if isinstance(other_label, Unknown):
                    continue

                # set value to 1 if tracks have the same label, 0 otherwise
                # make sure the matrix is symmetric
                y[t, T] = (label == other_label)
                y[T, t] = y[t, T]

        x = np.zeros((nTracks, nTracks), dtype=float)
        for t, (segment, track) in enumerate(allTracks):
            local_similarity = similarity[segment, track]
            for T, (other_segment, other_track) in enumerate(allTracks):
                x[t, T] = local_similarity[other_segment, other_track]

        # using squareform: we assume similarity is symmetric
        # also allows to get rid of self-similarity values (matrix diagonal)
        return squareform(x, checks=False).reshape((-1, 1)), \
            squareform(y, checks=False).reshape((-1, 1)), kwargs

    def train_mapping(self, X, Y, **kwargs):

        # remove NaNs
        ok = np.where(~np.isnan(X))
        x = X[ok]
        y = Y[ok]

        # positive & negative samples
        positive = x[np.where(y == 1)]
        negative = x[np.where(y == 0)]

        # score-to-log-likelihood-ratio mapping
        s2llr = sc2llr.computeLinearMapping(negative, positive)
        prior = 1. * len(positive) / (len(positive) + len(negative))

        return (s2llr, prior)

    def fit(self, training_data, **kwargs):
        """
        Fit calibration to training data

        Parameters
        ----------
        training_data : list
            List of (reference, tracks, similarity) tuples where each tuple is made of
            - `reference` annotation that can be None in case `tracks` are already labelled.
            - hypothesis `tracks` for the same resource
            - track-to-track `similarity` metric matrix
        kwargs : dict
            See .xy() method
        """

        X = []
        Y = []

        for data in training_data:
            # DEBUG
            print data[1].uri
            x, y, kwargs = self.xy(*data, **kwargs)
            X.append(x)
            Y.append(y)

        self.kwargs = kwargs
        self.X = np.vstack(X)
        self.Y = np.vstack(Y)

        self.mapping = self.train_mapping(self.X, self.Y, **(self.kwargs))

        return self

    def apply(self, similarity, tracks=None, prior=None):
        """
        Apply metric calibration

        Parameters
        ----------
        similarity : `pandas.DataFrame`
            Uncalibrated similarity metric matrix
        tracks : `Annotation`, optional
            Used in case `similarity` is a `LabelMatrix`
        prior : float, optional
            When provide, set manual prior p(x|H) to `prior`
            Uses estimated prior by default.

        Returns
        -------
        calibrated : `pandas.DataFrame`
            Calibrated similarity metric matrix

        """

        if isinstance(similarity, LabelMatrix):
            similarity = labelMatrix_to_dataFrame(similarity, tracks)

        (a, b), estimated_prior = self.mapping
        if not prior:
            prior = estimated_prior

        def s2p(x):
            # p(x|¬H)/p(x|H)
            lr = 1./np.exp(a*x+b)
            # p(¬H)/p(H)
            rho = (1.-prior)/prior
            return 1./(1.+rho*lr)

        return similarity.map(s2p)


def labelMatrix_to_dataFrame(similarity, tracks):
    """
    Convert old-school (LabelMatrix) track similarity matrix to DataFrame
    Only keep tracks available in both similarity matrix and segmentation.

    Parameters
    ----------
    similarity : `LabelMatrix`
        Track similarity matrix
    tracks : `Annotation`


    """

    ilabels, jlabels = similarity.labels

    # make sure ilabel and jlabel are identical
    if ilabels != jlabels:
        raise ValueError('Row/column mismatch')

    # make sure there is exactly one track per ilabel
    # save this track into `availableTracks` list
    availableTracks = []
    for i, ilabel in enumerate(ilabels):
        itracks = tracks.get_track_by_name(ilabel)
        if len(itracks) == 1:
            availableTracks.append(itracks[0])

    allTracks = [(segment, track) for segment, track in tracks.itertracks()]
    df = pandas.DataFrame(index=allTracks, columns=allTracks)
    for i, (isegment, itrack) in enumerate(availableTracks):
        for j, (jsegment, jtrack) in enumerate(availableTracks):
            try:
                df[isegment, itrack][jsegment, jtrack] = similarity[itrack, jtrack]
            except:
                pass

    return df

if __name__ == "__main__":

    import pickle
    import sys
    from argparse import ArgumentParser
    import pyannote.cli

    parser = ArgumentParser(description='Calibration of clustering metrics')
    subparsers = parser.add_subparsers(help='mode')

    # ==============
    # TRAIN mode
    # ==============

    def trainCalibration(args):
        uris = pyannote.cli.get_uris()
        if not uris:
            raise IOError('Empty list of resources. Please use --uris option.')

        def _get_tracks(uri):
            tracks = args.tracks(uri)
            if hasattr(args, 'uem'):
                uem = args.uem(uri)
                tracks = tracks.crop(uem, mode='loose')
            return tracks

        if hasattr(args, 'reference'):
            data = [(args.reference(uri), _get_tracks(uri), args.similarity(uri)) for uri in uris]
        else:
            data = [(None, _get_tracks(uri), args.similarity(uri)) for uri in uris]
        calibration = ClusteringCalibration().fit(data)
        with args.output() as f:
            pickle.dump(calibration, f)

    train_parser = subparsers.add_parser('train', help='Train calibration',
                                         parents=[pyannote.cli.parentArgumentParser()])
    train_parser.set_defaults(func=trainCalibration)

    description = 'path to input similarity metric matrices.'
    train_parser.add_argument('similarity', help=description,
                              type=pyannote.cli.InputGetMatrix())

    description = 'path to input tracks.'
    initArgs = {'load_ids': True}
    train_parser.add_argument('tracks', help=description,
                              type=pyannote.cli.InputGetAnnotation(initArgs=initArgs))

    description = 'path to output calibration.'
    train_parser.add_argument('output', help=description,
                              type=pyannote.cli.OutputFileHandle())

    description = 'path to input reference annotation.'
    train_parser.add_argument('--reference', help=description,
                              default=pyannote.cli.SUPPRESS,
                              type=pyannote.cli.InputGetAnnotation())

    # ==============
    # APPLY mode
    # ==============
    def applyCalibration(args):
        uris = pyannote.cli.get_uris()
        if not uris:
            raise IOError('Empty list of resources. Please use --uris option.')

        with args.calibration() as f:
            calibration = pickle.load(f)

        prior = args.prior if hasattr(args, 'prior') else None

        for uri in uris:

            similarity = args.similarity(uri)

            if hasattr(args, 'tracks'):
                similarity = labelMatrix_to_dataFrame(similarity, args.tracks(uri))

            calibrated = calibration.apply(similarity, prior=prior)
            with args.calibrated(uri=uri) as f:
                pickle.dump(calibrated, f)

    apply_parser = subparsers.add_parser('apply', help='Apply calibration',
                                         parents=[pyannote.cli.parentArgumentParser()])
    apply_parser.set_defaults(func=applyCalibration)

    description = 'path to input similarity metric matrices.'
    train_parser.add_argument('similarity', help=description,
                              type=pyannote.cli.InputGetMatrix())

    description = 'optional path to input tracks.'
    train_parser.add_argument('--tracks', help=description,
                              default=pyannote.cli.SUPPRESS,
                              type=pyannote.cli.InputGetAnnotation())

    description = 'path to input calibration.'
    apply_parser.add_argument('calibration', help=description,
                              type=pyannote.cli.InputFileHandle())

    description = 'path to output calibrated similarity metric matrices.'
    apply_parser.add_argument('calibrated', help=description,
                              type=pyannote.cli.OutputFileHandle())

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
        sys.stderr.write('%s' % e)
        sys.exit(-1)
