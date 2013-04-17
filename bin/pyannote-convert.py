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
import pyannote.cli
from argparse import SUPPRESS

argparser = pyannote.cli.initParser('Annotation file format conversion')

# Original annotation file
description = 'path to original annotation.' + pyannote.cli.URI_SUPPORT
argparser.add_argument('src', metavar='source',
                       type=pyannote.cli.InputGetAnnotation(),
                       help=description)

# Converted annotation file
description = 'path to converted annotation.' + pyannote.cli.URI_SUPPORT
argparser.add_argument('tgt', metavar='target',
                       type=pyannote.cli.OutputWriteAnnotation(),
                       help=description)


group = argparser.add_argument_group('Structure')

import numpy as np


def threshold_parser(value):
    if value in ['-oo', '+oo', 'oo', 'P']:
        if value == '-oo':
            return -np.inf
        elif value in ['+oo', 'oo']:
            return np.inf
        else:
            return None
    else:
        return float(value)

group.add_argument('--to-annotation', type=threshold_parser, metavar='THETA',
                   nargs='?', default=SUPPRESS, const=threshold_parser('-oo'),
                   help='convert scores to annotation. '
                        'if the score of the top-score label is higher than '
                        'THETA, then choose this label. otherwise, set label '
                        'to Unknown. Default THETA is "-oo". Use "P" to indicate '
                        'scores are posteriors.')

group.add_argument('--re-track', action='store_true',
                   help='rename tracks with unique identifiers')

group.add_argument('--compress', action='store_true',
                   help='compress annotation by making one track of '
                        'contiguous tracks with similar label. note '
                        'that track names will be lost.')

group.add_argument('--anonymize', action='store_true',
                   help='anonymize annotation by changing every label '
                        'to Unknown. two tracks with the same original '
                        'label will still have the same Unknown label.')

group.add_argument('--modality', action='append', dest='modalities', metavar='MODALITY',
                   default=[], help='only extract requested modality')

# Actual argument parsing
try:
    args = argparser.parse_args()
except IOError as e:
    sys.stderr.write('%s' % e)
    sys.exit(-1)


def structural_transforms(A):
    if hasattr(args, 'to_annotation'):
        if args.to_annotation is None:
            A = A.to_annotation(posterior=True)
        else:
            A = A.to_annotation(threshold=args.to_annotation)
    if args.compress:
        A = A.smooth()
    if args.anonymize:
        A = A.anonymize()
    if args.re_track:
        A = A.retrack()
    return A


# Obtain final list of URIs to process
# (either from --uri(s) options or from input files)
uris = pyannote.cli.get_uris()

# Process every resource, one after the other
for u, uri in enumerate(uris):

    if args.verbose:
        sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
        sys.stdout.flush()

    if args.modalities:

        for modality in args.modalities:

            src = args.src(uri, modality)

            if hasattr(args, 'uem'):
                uem = args.uem(uri)
                src = src.crop(uem, mode='intersection')

            tgt = structural_transforms(src)

            # Write to
            args.tgt(tgt)

    else:
        src = args.src(uri)

        if hasattr(args, 'uem'):
            uem = args.uem(uri)
            src = src.crop(uem, mode='intersection')

        tgt = structural_transforms(src)

        # Write to
        args.tgt(tgt)
