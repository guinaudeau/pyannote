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
from pyannote.parser import AnnotationParser
from pyannote.algorithm.clustering.util import LogisticProbabilityMaker

def speaker_diarization(args):
    
    from pyannote.parser import PLPParser
    from pyannote.algorithm.clustering.model.base import SimilarityMatrix
    from pyannote.algorithm.clustering.model import BICMMx
    from pyannote.algorithm.clustering.agglomerative.stop import NegativeSMx
    from pyannote.algorithm.clustering.util import label_clustering_groundtruth
    
    params = {}
    
    if args.similarity == 'bic':
        params['__mmx__'] = BICMMx
        params['__smx__'] = NegativeSMx
        params['penalty_coef'] = args.penalty_coef
        params['covariance_type'] = args.covariance_type
    elif args.similarity == 'clr':
        sys.exit('ERROR: CLR similarity not yet supported.\n')
        # params['__mmx__'] = CLRMMx
    elif args.similarity == 'ivector':
        sys.exit('ERROR: iVector similarity not yet supported.\n')
        # params['__mmx__'] = IVectorMMx
        
    class Matrix(SimilarityMatrix, params['__mmx__']):
        def __init__(self, **kwargs):
                super(Matrix, self).__init__(**params)
    
    matrix = Matrix()
    
    X = np.empty((0,1))
    Y = np.empty((0,1))
    
    # if requested, use provided resources
    if hasattr(args, 'uris'):
        uris = args.uris
    # otherwise, use all resources in input file
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
        if hasattr(args, 'uem'):
            uem = args.uem(uri)
            reference = reference(uem, mode='intersection')
            annotation = annotation(uem, mode='intersection')
        
        # get groundtruth
        y = label_clustering_groundtruth(reference, annotation)
        Y = np.append(Y, y.M)
        
        # load PLP features
        path = clicommon.replaceURI(args.plp, uri)
        feature = PLPParser().read(path)
        
        M = matrix(annotation, feature)
        
        X = np.append(X, M.M)
    
    params['__X__'] = X
    params['__Y__'] = Y
    params['__uris__'] = uris
    params['__s2p__'] = LogisticProbabilityMaker().fit(params['__X__'],
                                                       params['__Y__'],
                                                       prior=1.)
    # save to output file
    pickle.dump(params, args.output)
    args.output.close()

def face_clustering(args):
    
    from pyannote.parser import LabelMatrixParser
    from pyannote.base.annotation import Unknown
    
    params = {}
    
    X = []
    y = []
    
    for u, uri in enumerate(args.uris):
        
        if args.verbose:
            sys.stdout.write('[%d/%d] %s\n' % (u+1, len(args.uris), uri))
            sys.stdout.flush()
        
        # load pre-computed distance matrix
        path = clicommon.replaceURI(args.precomputed, uri)
        M = LabelMatrixParser().read(path)
        
        # load input annotation
        annotation = args.input(uri)
        if hasattr(args, 'uem'):
            uem = args.uem(uri)
            annotation = annotation(uem, mode='intersection')
        
        # focus on associated tracks
        labels = [l for l in annotation.labels() 
                        if not isinstance(l, Unknown)]
        annotation = annotation(labels)
        
        for l, label in enumerate(labels):
            t = annotation(label)
            other_t = annotation(label, invert=True)
            for _, track, _ in t.iterlabels():
                for _, other_track, _ in t.iterlabels():
                    if track == other_track:
                        continue
                    try:
                        X.append(M[track, other_track])
                        y.append(1)
                    except Exception, e:
                        pass
                for _, other_track, _ in other_t.iterlabels():
                    try:
                        X.append(M[track, other_track])
                        y.append(0)
                    except Exception, e:
                        pass
    
    params['__X__'] = np.array(X)
    params['__Y__'] = np.array(y)
    if hasattr(args, 'uris'):
        params['__uris__'] = args.uris
    params['__s2p__'] = LogisticProbabilityMaker().fit(params['__X__'],
                                                       params['__Y__'],
                                                       prior=1.)
    # save to output file
    pickle.dump(params, args.output)
    args.output.close()


from pyannote import clicommon
from argparse import ArgumentParser, SUPPRESS

argparser = ArgumentParser(description='A tool for clustering training')

subparsers = argparser.add_subparsers(help='commands')

# =========================
# == Speaker diarization ==
# =========================

sparser = subparsers.add_parser('speaker', parents=[clicommon.parser], 
                                           help='speaker diarization')
sparser.set_defaults(func=speaker_diarization)

def input_parser(path):
    return AnnotationParser().read(path)
sparser.add_argument('input', type=input_parser, metavar='source',
                       help='path to input annotation')

sparser.add_argument('reference', type=input_parser, metavar='target', 
                       help='path to expected output annotation')

msg = "path to PLP feature files. " \
      "URI placeholders are supported: %s." % " or ".join(clicommon.URIS[1:])
sparser.add_argument('plp', type=str, metavar='file.plp', help=msg)

def output_parser(path):
    try:
       with open(path) as f: pass
    except IOError as e:
       return open(path, 'w')
    raise IOError('ERROR: output file %s already exists. Delete it first.\n' % path)
sparser.add_argument('output', type=output_parser, metavar='params.pkl',
                     help='path to output file')

# Speech turn similarity
sparser.add_argument('--similarity', choices=('bic', 'clr', 'ivector'),
                     help='choose speech turn similarity measure '
                     '(default: bic)',
                     default='bic')

# -- BIC --
sparser.add_argument('--penalty', dest='penalty_coef', type=float, 
                     default=3.5, metavar='λ', 
                     help='BIC penalty coefficient (default: 3.5). '
                          'smaller λ means purer clusters.')
sparser.add_argument('--diagonal', dest='covariance_type', 
                     action='store_const', const='diag', default='full',
                     help='use diagonal covariance matrix (default: full)')

# =====================
# == Face clustering ==
# =====================

fparser = subparsers.add_parser('face', parents=[clicommon.parser],
                                        help='face clustering')
fparser.set_defaults(func=face_clustering)

def input_fparser(path):
    if clicommon.containsURI(path):
        return lambda u: AnnotationParser(load_ids=True)\
                         .read(clicommon.replaceURI(path, u), video=u)(u)
        # load_ids = True makes unassociated tracks labeled as Unknown()
        # associated tracks are labeled with the person identity
    else:
        return AnnotationParser().read(path)

msg = "path to input associated tracks. " \
      "URI placeholders are supported: %s." % " or ".join(clicommon.URIS[1:])
fparser.add_argument('input', type=input_fparser, metavar='input', help=msg)

msg = "path to precomputed similarity matrix. " \
      "URI placeholders are supported: %s." % " or ".join(clicommon.URIS[1:])
fparser.add_argument('precomputed', type=str, metavar='matrix',
                     help=msg)

fparser.add_argument('output', type=output_parser, metavar='params.pkl',
                     help='path to output file')

# Actual argument parsing
try:
    args = argparser.parse_args()
except Exception, e:
    sys.exit(e)

args.func(args)
