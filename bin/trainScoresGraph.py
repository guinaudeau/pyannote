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


import sys
import pickle
import numpy as np
import pyannote
from pyannote.base.annotation import Annotation, Unknown, Timeline
from pyannote.parser.annotation import AnnotationParser
from pyannote.algorithm.clustering.util import LogisticProbabilityMaker
from pyannote.algorithm.tagging import ArgMaxDirectTagger

def speaker_identification(args):

    # if requested, use provided resources
    if hasattr(args, 'uris'):
        uris = args.uris

    # otherwise, use all resources in input file
    else:
        uris = args.reference.uris

    tagger = ArgMaxDirectTagger()
    X = []
    Y = []

    for u, uri in enumerate(uris):

        # verbosity
        if args.verbose:
            sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
            sys.stdout.flush()

        # reference annotation
        reference = args.reference(uri)

        # identification scores
        scores = args.scores(uri)

        # focus on UEM
        if hasattr(args, 'uem'):
            uem = args.uem(uri)
            reference = reference.crop(uem, mode='intersection')
            scores = scores.crop(uem, mode='intersection')

        # new annotation with same tracks as `scores`
        # all labels are set to Unknown
        t = scores.to_annotation(threshold=np.inf)

        # propagate reference labels to t
        # for each track in t,
        T = tagger(reference, t)

        # list of all available models
        models = scores.labels()

        # loop on every track in `scores`
        for segment, track, label in T.itertracks(label=True):

            # if label is Unknown, it means that no label was propagated
            # from reference --> skip this track
            if isinstance(label, Unknown):
                continue

            for model in models:

                # if score is not available for this model (nan)
                # --> skip this model
                value = scores[segment, track, model]
                if np.isnan(value):
                    continue

                # otherwise, add score to the list
                X.append(value)

                # add groundtruth status to the list
                if model == label:
                    Y.append(1)
                else:
                    Y.append(0)

    X = np.array(X)
    Y = np.array(Y)

    params = {}
    params['__uris__'] = uris
    params['__X__'] = X
    params['__Y__'] = Y

    try:
        s2p = LogisticProbabilityMaker().fit(X, Y, prior=1.)
        params['__s2p__'] = s2p
    except Exception, e:
        print "Could not fit logistic probability maker"

    # save to output file
    pickle.dump(params, args.output)
    args.output.close()

def face_recognition(args):

    X = []
    Y = []

    uris = args.uris

    for u, uri in enumerate(uris):

        if args.verbose:
            sys.stdout.write('[%d/%d] %s\n' % (u+1, len(args.uris), uri))
            sys.stdout.flush()

        # load input annotation and scores
        annotation = args.input(uri)
        scores = args.scores(uri)

        # focus on annotated region ...
        if hasattr(args, 'uem'):
            uem = args.uem(uri)
            annotation = annotation.crop(uem, mode='loose')
            scores = scores.crop(uem, mode='loose')

        # ... and annotated tracks
        labels = [l for l in annotation.labels()
                        if not isinstance(l, Unknown)]
        annotation = annotation.subset(set(labels))

        # loop on tracks for which scores were computed
        for s,t,l in annotation.itertracks(label=True):

            if not scores.has_track(s,t):
                continue

            for L,V in scores.get_track_scores(s,t).iteritems():
                Y.append(int(l==L))
                X.append(V)


    X = np.array(X)
    Y = np.array(Y)

    params = {}
    params['__uris__'] = uris
    params['__X__'] = X
    params['__Y__'] = Y

    try:
        s2p = LogisticProbabilityMaker().fit(X, Y, prior=1.)
        params['__s2p__'] = s2p
    except Exception, e:
        print "Could not fit logistic probability maker"

    pickle.dump(params, args.output)
    args.output.close()


from pyannote import clicommon
from argparse import ArgumentParser, SUPPRESS

argparser = ArgumentParser(description='Scores graph training')

subparsers = argparser.add_subparsers(help='commands')

# =========================
# == Speaker diarization ==
# =========================

sparser = subparsers.add_parser('speaker', parents=[clicommon.parser],
                                           help='speaker identification')
sparser.set_defaults(func=speaker_identification)

def scores_parser(path):
    return AnnotationParser().read(path)
sparser.add_argument('scores', type=scores_parser, metavar='source.etf0',
                       help='path to etf0 file.')

def ref_parser(path):
    return AnnotationParser().read(path)
sparser.add_argument('reference', type=ref_parser, metavar='reference.mdtm',
                       help='path to reference')

def output_parser(path):
    try:
       with open(path) as f: pass
    except IOError as e:
       return open(path, 'w')
    raise IOError('ERROR: output file %s already exists. Delete it first.\n' % path)
sparser.add_argument('output', type=output_parser, metavar='params.pkl',
                     help='path to output file')

# =====================
# == Face clustering ==
# =====================

fparser = subparsers.add_parser('face', parents=[clicommon.parser],
                                        help='face recognition')
fparser.set_defaults(func=face_recognition)

def input_fparser(path):
    if clicommon.containsURI(path):
        return lambda u: AnnotationParser(load_ids=True)\
                         .read(clicommon.replaceURI(path, u), uri=u)(u)
        # load_ids = True makes unassociated tracks labeled as Unknown()
        # associated tracks are labeled with the person identity
    else:
        raise IOError('Only .facetracks input files are supported for now.')

msg = "path to input associated tracks. " + clicommon.msgURI()
fparser.add_argument('input', type=input_fparser, metavar='input', help=msg)


def scores_fparser(path):
    if clicommon.containsURI(path):
        return lambda u: AnnotationParser()\
                         .read(clicommon.replaceURI(path, u), uri=u)(u)
    else:
        return AnnotationParser().read(path)

msg = "path to precomputed distances to models. " + clicommon.msgURI()
fparser.add_argument('scores', type=scores_fparser, metavar='scores',
                     help=msg)

fparser.add_argument('output', type=output_parser, metavar='params.pkl',
                     help='path to output file')

# Actual argument parsing
try:
    args = argparser.parse_args()
except Exception, e:
    sys.exit(e)

args.func(args)
