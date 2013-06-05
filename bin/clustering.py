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
from pyannote.parser.annotation import AnnotationParser
from pyannote.parser.mdtm import MDTMParser
from pyannote.algorithm.clustering.agglomerative.base import AgglomerativeClustering, MatrixIMx
from pyannote.algorithm.clustering.model import AverageLinkMMx, CompleteLinkMMx, SingleLinkMMx
from pyannote.algorithm.clustering.agglomerative.constraint import ContiguousCMx, CooccurringCMx


def speaker_diarization(args):

    from pyannote.parser.plp import PLPParser
    from pyannote.algorithm.clustering.model import BICMMx
    from pyannote.algorithm.clustering.agglomerative.stop import NegativeSMx

    params = {}

    if args.similarity == 'bic':
        params['__mmx__'] = BICMMx
        params['__smx__'] = NegativeSMx
        params['penalty_coef'] = args.penalty_coef
        params['covariance_type'] = args.covariance_type
    elif args.similarity == 'clr':
        sys.exit('ERROR: CLR similarity not yet supported.\n')
    elif args.similarity == 'ivector':
        sys.exit('ERROR: iVector similarity not yet supported.\n')

    debug = len(args.verbose) > 1

    if hasattr(args, 'tolerance'):
        params['tolerance'] = args.tolerance
        class Clustering(AgglomerativeClustering, MatrixIMx,
                         ContiguousCMx, CooccurringCMx,
                         params['__mmx__'], params['__smx__']):
            def __init__(self, **kwargs):
                super(Clustering, self).__init__(debug=debug, **params)
    else:
        class Clustering(AgglomerativeClustering, MatrixIMx,
                         CooccurringCMx,
                         params['__mmx__'], params['__smx__']):
            def __init__(self, **kwargs):
                super(Clustering, self).__init__(debug=debug, **params)

    clustering = Clustering()

    # if requested, use provided resources
    if hasattr(args, 'uris'):
        uris = args.uris
    # otherwise, use all resources in input file
    else:
        uris = args.input.uris

    for u, uri in enumerate(uris):

        if args.verbose:
            sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
            sys.stdout.flush()

        # load input annotation
        annotation = args.input(uri)
        if hasattr(args, 'uem'):
            uem = args.uem(uri)
            annotation = annotation.crop(uem, mode='intersection')

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

    from pyannote.parser.matrix import LabelMatrixParser
    from pyannote.algorithm.clustering.agglomerative.stop import LessThanSMx, NumberOfClustersSMx

    params = {}
    if hasattr(args, 'smaller'):
        params['__smx__'] = LessThanSMx
        params['threshold'] = args.smaller
    elif hasattr(args, 'nclusters'):
        params['__smx__'] = NumberOfClustersSMx
        params['num_clusters'] = args.nclusters

    if hasattr(args, 'tolerance'):
        params['tolerance'] = args.tolerance

    params['debug'] = len(args.verbose) > 1

    if hasattr(args, 'tolerance'):
        if args.cooccurring:
            class Clustering(AgglomerativeClustering, MatrixIMx, ContiguousCMx,
                             args.linkage, params['__smx__']):
                def __init__(self, **kwargs):
                    super(Clustering, self).__init__(**params)
        else:
            class Clustering(AgglomerativeClustering, MatrixIMx, ContiguousCMx,
                             CooccurringCMx, args.linkage, params['__smx__']):
                def __init__(self, **kwargs):
                    super(Clustering, self).__init__(**params)
    else:
        if args.cooccurring:
            class Clustering(AgglomerativeClustering, MatrixIMx,
                             args.linkage, params['__smx__']):
                def __init__(self, **kwargs):
                    super(Clustering, self).__init__(**params)
        else:
            class Clustering(AgglomerativeClustering, MatrixIMx,
                             CooccurringCMx, args.linkage, params['__smx__']):
                def __init__(self, **kwargs):
                    super(Clustering, self).__init__(**params)

    clustering = Clustering()

    # if requested, use provided resources
    if hasattr(args, 'uris'):
        uris = args.uris
    # otherwise, use all resources in input file
    else:
        uris = args.input.uris

    # add header to output file
    args.output.write('# PyAnnote %s\n' % pyannote.__version__)

    for u, uri in enumerate(uris):

        if args.verbose:
            sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
            sys.stdout.flush()

        # load input annotation
        annotation = args.input(uri)
        if hasattr(args, 'uem'):
            uem = args.uem(uri)
            annotation = annotation.crop(uem, mode='intersection')

        # load pre-computed distance matrix
        path = clicommon.replaceURI(args.precomputed, uri)
        matrix = LabelMatrixParser().read(path)

        # convert distance/similarity matrix to probability
        matrix.M = args.s2p(matrix.M)

        # matrix might be incomplete
        # clustering can only be done when similarity matrix is available
        labels, _ = matrix.labels
        available = annotation(labels)
        # perform actual clustering
        output = clustering(available, matrix)

        # save final similarity matrix
        if hasattr(args, 'dump'):
            with args.dump(uri) as f:
                matrix = clustering.imx_matrix
                pickle.dump(matrix, f)

        # add remaining annotations back to the original output
        unavailable = annotation(labels, invert=True)
        for s, t, l in unavailable.iterlabels():
            output[s, t] = l

        # save to file
        MDTMParser().write(output, f=args.output)


    # close output file
    args.output.close()


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

msg = "path to PLP feature files." + clicommon.msgURI()
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
        return lambda u: AnnotationParser(load_ids=False)\
                         .read(clicommon.replaceURI(path, u), uri=u)(u)
    else:
        return AnnotationParser().read(path)

msg = "path to input annotation." + clicommon.msgURI()
fparser.add_argument('input', type=input_fparser, metavar='input', help=msg)

msg = "path to precomputed similarity matrix." + clicommon.msgURI()
fparser.add_argument('precomputed', type=str, metavar='matrix',
                     help=msg)

fparser.add_argument('output', type=output_parser, metavar='output.mdtm',
                     help='path to where to store output in MDTM format')

group = fparser.add_argument_group('Agglomerative clustering')
linkage = group.add_mutually_exclusive_group()
linkage.add_argument('--average-link', action='store_const', dest='linkage',
                     const=AverageLinkMMx, default=AverageLinkMMx,
                     help='average-link agglomerative clustering '
                          '(default)')
linkage.add_argument('--complete-link', action='store_const', dest='linkage',
                     const=CompleteLinkMMx, default=AverageLinkMMx,
                     help='complete-link agglomerative clustering')
linkage.add_argument('--single-link', action='store_const', dest='linkage',
                     const=SingleLinkMMx, default=AverageLinkMMx,
                     help='single-link agglomerative clustering')

def params_fparser(path):
    with open(path, 'r') as f:
        params = pickle.load(f)
    return params['__s2p__']
group.add_argument('--to-probability', dest='s2p', type=params_fparser,
                     metavar='params.pkl', default=(lambda M: M),
                     help='turn similarity into probability using '
                          'parameters trained previously')

group = fparser.add_argument_group('Stopping criterion')

stop = group.add_mutually_exclusive_group()
stop.add_argument('--smaller', type=float, metavar='THETA', default=SUPPRESS,
                   help='stop merging when similarity (or probability) '
                        'is smaller than THETA.')
stop.add_argument('--nclusters', type=int, metavar='K', default=SUPPRESS,
                   help='stop merging when number of clusters is below K.')

def output_fparser(path):

    if clicommon.containsURI(path):

        def f(uri):
            new_path = clicommon.replaceURI(path, uri)
            try:
               with open(new_path) as f: pass
            except IOError as e:
               return open(new_path, 'w')
            raise IOError('ERROR: output file %s already exists. '
                          'Delete it first.\n' % new_path)

        return f

    else:
        raise IOError('ERROR: missing URI placeholders')

msg = "(pickle-)dump updated similarity matrix." + clicommon.msgURI()
fparser.add_argument('--dump', type=output_fparser, default=SUPPRESS,
                     metavar='matrix.pkl', help=msg)

# -- Linear clustering --

group = fparser.add_argument_group('Constraints')
group.add_argument('--linear',
        type=float, metavar='DELTA', default=SUPPRESS, dest='tolerance',
        help='only allow mergin of two face tracks far apart '
             'by less than DELTA seconds')
group.add_argument('--cooccurring', action='store_true',
                   help='allow merging of two cooccurring face tracks '
                        '(default behavior is to prevent merging of two '
                        'faces appearing simultaneously.)')

try:
    args = argparser.parse_args()
except Exception, e:
    sys.exit(e)

args.func(args)
