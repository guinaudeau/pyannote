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

def src_parser(path):
    return AnnotationParser().read(path)
argparser.add_argument('src', type=src_parser, metavar='source',
                       help='path to source annotation')

def out_parser(path):
    try:
       with open(path) as f: pass
    except IOError as e:
        writer, extension = AnnotationParser.guess(path)
        return writer(), open(path, 'w')
    raise IOError('ERROR: output file %s already exists. Delete it first.\n' % path)

argparser.add_argument('tgt', type=out_parser, metavar='target',
                       help='path to target annotation')

group = argparser.add_argument_group('modality name conversion')
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

try:
   args = argparser.parse_args()
except IOError as e:
   sys.stderr.write('%s' % e)
   sys.exit(-1)

src_modalities = args.src.modalities
uris = args.src.videos

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

for u, uri in enumerate(uris):
    
    # Verbosity
    if args.verbose:
        sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
        sys.stdout.flush()
    
    # Modality name conversion
    for modality in src_modalities:
        src = args.src(video=uri, modality=modality)
        if modality in convert_modality:
            src.modality = convert_modality[modality]
        writer.write(src, f=f)

f.close()
    