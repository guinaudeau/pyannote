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
from argparse import ArgumentParser, SUPPRESS
from pyannote.parser import AnnotationParser

from pyannote import clicommon
argparser = ArgumentParser(parents=[clicommon.parser], 
                           description='A tool for annotation file conversion')


srcContainsURI = False

def src_parser(path):
    if clicommon.containsURI(path):
        global srcContainsURI
        srcContainsURI = True
        return lambda u: AnnotationParser()\
                         .read(clicommon.replaceURI(path, u), uri=u)(u)
    else:
        return AnnotationParser().read(path)

msg = 'path to source annotation. ' + clicommon.msgURI()
argparser.add_argument('src', type=src_parser, metavar='source', help=msg)

def out_parser(path):
    try:
       with open(path) as f: pass
    except IOError as e:
        writer, extension = AnnotationParser.guess(path)
        return writer(), open(path, 'w')
    raise IOError('ERROR: output file %s already exists. Delete it first.\n' % path)

argparser.add_argument('tgt', type=out_parser, metavar='target',
                       help='path to target annotation')

group = argparser.add_argument_group('Modality conversion')
group.add_argument('-mi', type=str, metavar='old', 
                   action='append', dest='modality_old', default=[],
                   help='input modality name')
group.add_argument('-mo', type=str, metavar='new',
                   action='append', dest='modality_new', default=[],
                   help='output modality name. '
                        'when combined with -mi old option, modality name '
                        'is converted from old to new. '
                        'when used on its own, any old modality name '
                        'is convert to new.')


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

try:
   args = argparser.parse_args()
except IOError as e:
   sys.stderr.write('%s' % e)
   sys.exit(-1)

if not srcContainsURI:
    src_modalities = args.src.modalities

if not srcContainsURI:
    uris = args.src.uris

# if list of resources is provided, use it.
if hasattr(args, 'uris'):
    uris = args.uris

# modality conversion
convert_modality = {}

if args.modality_old:
    if len(args.modality_old) != len(args.modality_new):
        sys.stderr.write('ERROR: old/new modality number mismatch.\n')
        sys.exit(-1)
    convert_modality = {old:args.modality_new[o]
                        for o, old in enumerate(args.modality_old)}
elif len(args.modality_new) == 1:
    convert_modality = {old:args.modality_new[0] for old in src_modalities}

writer, f = args.tgt

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

for u, uri in enumerate(uris):

    # Verbosity
    if args.verbose:
        sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
        sys.stdout.flush()
    
    if srcContainsURI:
        src = args.src(uri)
        if src.modality in convert_modality:
            src.modality = convert_modality[src.modality]
        writer.write(structural_transforms(src), f=f)
    else:
        # Modality name conversion
        for modality in src_modalities:
            src = args.src(uri=uri, modality=modality)
            if modality in convert_modality:
                src.modality = convert_modality[modality]
            writer.write(structural_transforms(src), f=f)

f.close()
    