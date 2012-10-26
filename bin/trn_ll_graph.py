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
from argparse import ArgumentParser, SUPPRESS
from pyannote.parser import AnnotationParser, TimelineParser, LSTParser
from pyannote.parser import PLPParser
from pyannote.algorithm.clustering.util import label_clustering_groundtruth, LogisticProbabilityMaker
from pyannote.algorithm.clustering.model.base import SimilarityMatrix
from pyannote.algorithm.clustering.model.gaussian import BICMMx

from pyannote.parser.repere.facetracks import FACETRACKSParser
from pyannote.parser.repere.metric import METRICParser
from pyannote.base.annotation import Unknown

from pyannote import clicommon

def do_speaker(args):
    
    data = {}
    
    # In case of BIC similarity, make sure we got all needed parameters
    if args.bic:
        covariance_type = 'diag' if args.diagonal else 'full'
        penalty_coef = args.penalty
        if not hasattr(args, 'plp'):
            sys.stderr.write('Needed --plp argument for BIC similarity')
            sys.exit()
        class Dummy(SimilarityMatrix, BICMMx):
            pass
        bicSimilarityMatrix = Dummy(penalty_coef=penalty_coef, 
                                    covariance_type=covariance_type)
        data['covariance_type'] = covariance_type
        data['penalty_coef'] = penalty_coef
        data['MMx'] = BICMMx

    X = np.empty((0,1))
    Y = np.empty((0,1))

    # Use a URI subset
    if args.uris is not None:
        uris = args.uris
    else:
        uris = args.reference.videos

    for u, uri in enumerate(uris):
    
        # Verbosity
        if args.verbose:
            sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
            sys.stdout.flush()
    
        # reference segmentation
        reference = args.reference(uri)
        # input segmentation
        annotation = args.input(uri)
    
        # focus on UEM
        if args.uem is not None:
            uem = args.uem(uri)
            reference = reference(uem, mode='intersection')
            annotation = annotation(uem, mode='intersection')
    
        # get groundtruth
        y = label_clustering_groundtruth(reference, annotation)
        Y = np.append(Y, y.M)
    
        # get similarity 
        if args.bic:
        
            # PLP features
            path = clicommon.replaceURIs(args.plp, uri)
            feature = PLPParser().read(path)
            x = bicSimilarityMatrix(annotation, feature)
    
        X = np.append(X, x.M)
    
    # save to output file
    data['X'] = X
    data['Y'] = Y
    data['uris'] = uris
    
    lpm = LogisticProbabilityMaker()
    lpm.fit(X, Y, prior=1.)
    data['func'] = lpm
    
    f = open(args.save, 'w')
    pickle.dump(data, f)
    f.close()

def do_face(args):
    
    # load_ids = True makes unassociated tracks labeled as Unknown()
    # associated tracks are labeled with the person identity
    ft_parser = FACETRACKSParser(load_ids=True)
    mat_parser = METRICParser(aggregation='average')
    
    X = []
    y = []
    
    for u, uri in enumerate(args.uris):
        
        # Verbosity
        if args.verbose:
            sys.stdout.write('[%d/%d] %s\n' % (u+1, len(args.uris), uri))
            sys.stdout.flush()
        
        # load face tracks
        path = clicommon.replaceURIs(args.tracks, uri)
        T = ft_parser.read(path, video=uri)(uri)
        T = T(args.uem(uri), mode='loose')
        labels = [label for label in T.labels() 
                        if not isinstance(label, Unknown)]
        
        # load distance matrix
        path = clicommon.replaceURIs(args.metric, uri)
        D = mat_parser.read(path)
        
        # list of labels with at least one associated track
        for l, label in enumerate(labels):
            t = T(label)
            other_t = T(label, invert=True)
            for _, track, _ in t.iterlabels():
                for _, other_track, _ in t.iterlabels():
                    if track == other_track:
                        continue
                    try:
                        X.append(D[track, other_track])
                        y.append(1)
                    except:
                        pass
                for _, other_track, _ in other_t.iterlabels():
                    try:
                        X.append(D[track, other_track])
                        y.append(0)
                    except:
                        pass
    
    # save to output file
    data = {}
    data['X'] = np.array(X)
    data['Y'] = np.array(y)
    data['uris'] = args.uris
    f = open(args.save, 'w')
    pickle.dump(data, f)
    f.close()


argparser = ArgumentParser(description='A tool for training label similarity graphs')

def input_parser(path):
    return AnnotationParser().read(path)
def uem_parser(path):
    return TimelineParser().read(path)
def uris_parser(path):
    return LSTParser().read(path)

subparsers = argparser.add_subparsers(help='commands')

parser_speaker = subparsers.add_parser('speaker', parents=[clicommon.parser], 
                                       help='speaker diarization')
parser_speaker.set_defaults(func=do_speaker)

parser_face = subparsers.add_parser('face', parents=[clicommon.parser],
                                    help='face clustering')
parser_face.set_defaults(func=do_face)


# Second positional argument is input segmentation file
# -- loaded at argument-parsing time by an instance of AnnotationParser
parser_speaker.add_argument('input', metavar='source', type=input_parser,
                       help='path to input segmentation file')

# First positional argument is reference segmentation file
# -- loaded at argument-parsing time by an instance of AnnotationParser
parser_speaker.add_argument('reference', metavar='target', type=input_parser,
                       help='path to reference segmentation file')

# PLP features
msg = "path to PLP feature files. " \
      "URI placeholders are supported: %s." % " or ".join(clicommon.URIS[1:])
parser_speaker.add_argument('plp', type=str, metavar='file.plp', help=msg)

# Next positional argument is where to save parameters
parser_speaker.add_argument('save', type=str, metavar='output.pkl',
                        help='path to output file')


# BIC similarity
parser_speaker.add_argument('--bic', action='store_true',
                       help='use BIC as similarity metric')

# BIC penalty coefficient
parser_speaker.add_argument('--penalty', metavar='λ', type=float, default=3.5,
                       help='BIC penalty coefficient (default: 3.5)')

# Diagonal covariance matrix
parser_speaker.add_argument('--diagonal', action='store_true', 
                       help='use diagonal covariance matrix (default: full)')

# == Face clustering ==

# Training set -- loaded at argument-parsing time by an instance of LSTParser
parser_face.add_argument('uris', type=uris_parser, 
                       help='path to list used for training')

# UEM file is loaded at argument-parsing time by an instance of TimelineParser
parser_face.add_argument('uem', type=uem_parser, 
                       help='path to Unpartitioned Evaluation Map (UEM) file')

# .mat files
msg = "path to .mat files. " \
      "URI placeholders are supported: %s." % " or ".join(clicommon.URIS[1:])
parser_face.add_argument('metric', type=str, metavar='file.mat', help=msg)

msg = "path to .facetracks files. " \
      "URI placeholders are supported: %s." % " or ".join(clicommon.URIS[1:])
parser_face.add_argument('tracks', type=str, 
                         metavar='file.facetracks', help=msg)

# Next positional argument is where to save parameters
parser_face.add_argument('save', type=str, metavar='output',
                        help='path to output file')

# Actual argument parsing
args = argparser.parse_args()
args.func(args)
