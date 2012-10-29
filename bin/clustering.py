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
import pyannote
from pyannote.parser import AnnotationParser, MDTMParser
from pyannote.algorithm.clustering.agglomerative.base import AgglomerativeClustering, MatrixIMx
from pyannote.algorithm.clustering.agglomerative.constraint import ContiguousCMx

def speaker_diarization(args):
    
    from pyannote.parser import PLPParser
    from pyannote.algorithm.clustering.model import BICMMx
    from pyannote.algorithm.clustering.agglomerative.stop import NegativeSMx
    
    if args.similarity == 'bic':
        mmx = BICMMx
        smx = NegativeSMx
    elif args.similarity == 'clr':
        sys.exit('ERROR: CLR similarity not yet supported.\n')
    elif args.similarity == 'ivector':
        sys.exit('ERROR: iVector similarity not yet supported.\n')
    
    debug = len(args.verbose) > 1
    
    if hasattr(args, 'tolerance'):
        class Clustering(AgglomerativeClustering, MatrixIMx, \
                         ContiguousCMx, mmx, smx):
            def __init__(self, **kwargs):
                super(Clustering, self).__init__(penalty_coef=args.penalty_coef,
                                           covariance_type=args.covariance_type,
                                           tolerance=args.tolerance,
                                           debug=debug,
                                           **kwargs)
    else:
        class Clustering(AgglomerativeClustering, MatrixIMx, \
                         mmx, smx):
            def __init__(self, **kwargs):
                super(Clustering, self).__init__(penalty_coef=args.penalty_coef,
                                           covariance_type=args.covariance_type,
                                           debug=debug,
                                           **kwargs)
    
    clustering = Clustering()
    
    # if requested, use provided resources
    if hasattr(args, 'uris'):
        uris = args.uris
    # otherwise, use all resources in input file
    else:
        uris = args.input.videos
    
    for u, uri in enumerate(uris):
        
        if args.verbose:
            sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
            sys.stdout.flush()
        
        # load input annotation
        annotation = args.input(uri)
        if hasattr(args, 'uem'):
            uem = args.uem(uri)
            annotation = annotation(uem, mode='intersection')
        
        # load PLP features
        path = clicommon.replaceURI(args.plp, uri)
        feature = PLPParser().read(path)
        
        # perform actual clustering
        output = clustering(annotation, feature)
        
        # save to file
        MDTMParser().write(output, f=args.output)
    
    # close output file
    args.output.close()
    
def face_clustering(args):
    pass

from pyannote import clicommon
from argparse import ArgumentParser, SUPPRESS
argparser = ArgumentParser(description='A tool for agglomerative clustering.')

subparsers = argparser.add_subparsers(help='commands')
sparser = subparsers.add_parser('speaker', parents=[clicommon.parser], 
                                       help='speaker diarization')
sparser.set_defaults(func=speaker_diarization)

def input_sparser(path):
    return AnnotationParser().read(path)
sparser.add_argument('input', type=input_sparser, metavar='input',
                       help='path to input annotation.')

def output_parser(path):
    try:
       with open(path) as f: pass
    except IOError as e:
       return open(path, 'w')
    raise IOError('ERROR: output file %s already exists. '
                  'Delete it first.\n' % path)
sparser.add_argument('output', type=output_parser, metavar='output.mdtm',
                     help='path to where to store output in MDTM format')

msg = "path to PLP feature files. " \
      "URI placeholders are supported: %s." % " or ".join(clicommon.URIS[1:])
sparser.add_argument('--plp', type=str, metavar='file.plp', help=msg)

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

# -- Linear clustering --
sparser.add_argument('--linear', 
        type=float, metavar='𝛿', default=SUPPRESS, dest='tolerance',
        help='only allow clustering of two speech turns far apart by less than 𝛿 seconds')

# =====================
# == Face clustering ==
# =====================

fparser = subparsers.add_parser('face', parents=[clicommon.parser],
                                help='face clustering')
fparser.set_defaults(func=face_clustering)

def input_fparser(path):
    if clicommon.containsURI(path):
        return lambda u: AnnotationParser().read(clicommon.replaceURI(path, u))
    else:
        return AnnotationParser().read(path)

msg = "path to input annotation. " \
      "URI placeholders are supported: %s." % " or ".join(clicommon.URIS[1:])
fparser.add_argument('input', type=input_fparser, metavar='input', help=msg)

fparser.add_argument('output', type=output_parser, metavar='output.mdtm',
                     help='path to where to store output in MDTM format')

fparser.add_argument('--linkage', choices=('average', 'complete', 'single'),
                     help='choose between average-, complete- or single-link '
                          'agglomerative clustering (default: average)',
                     default='average')

# fparser.add_argument('--similarity', choices=('precomputed',),
#                      help='choose face track similarity measure '
#                      '(default: precomputed)', default='precomputed')

def in_matrix_fparser():
    pass
msg = "path to precomputed similarity matrix. " \
      "URI placeholders are supported: %s." % " or ".join(clicommon.URIS[1:])
fparser.add_argument('--matrix', type=in_matrix_fparser, metavar='precomputed',
                      help=msg)

def out_matrix_fparser():
    pass
msg = "path where to save new similarity matrix. " \
      "URI placeholders are supported: %s." % " or ".join(clicommon.URIS[1:])
fparser.add_argument('--save-matrix', type=out_matrix_fparser, help=msg)

fparser.add_argument('--convert', type=str, metavar='params.pkl',
                     help='path to similarity-to-probability converter.')

# -- Linear clustering --
fparser.add_argument('--linear', 
        type=float, metavar='𝛿', default=SUPPRESS, dest='tolerance',
        help='only allow clustering of two face tracks far apart by less than 𝛿 seconds')


try:
    args = argparser.parse_args()
except Exception, e:
    sys.exit(e)

args.func(args)
