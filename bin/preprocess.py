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

def speaker_diarization(args):
    pass
    
def face_clustering(args):
    
    from pyannote.parser import LabelMatrixParser
    
    # if requested, use provided resources
    if hasattr(args, 'uris'):
        uris = args.uris
    # otherwise, use all resources in input file
    else:
        uris = args.input.videos
    
    # add header to output file
    args.output.write('# PyAnnote %s\n' % pyannote.__version__)
    
    for u, uri in enumerate(uris):
        
        if args.verbose:
            sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
            sys.stdout.flush()
        
        # load pre-computed distance matrix
        path = clicommon.replaceURI(args.precomputed, uri)
        matrix = LabelMatrixParser().read(path)
        
        # load input annotation
        annotation = args.input(uri)
        
        # remove small tracks
        if hasattr(args, 'small_tracks'):
            small_tracks = args.small_tracks(uri)
            annotation = annotation(small_tracks, invert=True)
        
        # remove tracks for which no distance is available
        if args.no_distance:
            labels, _ = matrix.labels
            annotation = annotation(labels)
        
        if hasattr(args, 'uem'):
            uem = args.uem(uri)
            annotation = annotation(uem, mode='intersection')
        
        # save reduced annotation
        MDTMParser().write(annotation, f=args.output)
        
        # save reduced similarity matrix
        if hasattr(args, 'dump'):
            labels = annotation.labels()
            matrix = matrix[set(labels), set(labels)]
            with args.dump(uri) as f:
                pickle.dump(matrix, f)
        
    # close output file
    args.output.close()

from pyannote import clicommon
from argparse import ArgumentParser, SUPPRESS

argparser = ArgumentParser(description='Pre-processing for face clustering.')

subparsers = argparser.add_subparsers(help='commands')
sparser = subparsers.add_parser('speaker', parents=[clicommon.parser], 
                                       help='speaker diarization')
sparser.set_defaults(func=speaker_diarization)

def output_parser(path):
    try:
       with open(path) as f: pass
    except IOError as e:
       return open(path, 'w')
    raise IOError('ERROR: output file %s already exists. '
                  'Delete it first.\n' % path)

# =====================
# == Face clustering ==
# =====================

fparser = subparsers.add_parser('face', parents=[clicommon.parser],
                                help='face clustering')
fparser.set_defaults(func=face_clustering)

def input_fparser(path):
    if clicommon.containsURI(path):
        return lambda u: AnnotationParser(load_ids=False)\
                         .read(clicommon.replaceURI(path, u), video=u)(u)
    else:
        return AnnotationParser().read(path)

msg = "path to input annotation." + clicommon.msgURI()
fparser.add_argument('input', type=input_fparser, metavar='input', help=msg)

msg = "path to precomputed similarity matrix." + clicommon.msgURI() 
fparser.add_argument('precomputed', type=str, metavar='matrix',
                     help=msg)

fparser.add_argument('output', type=output_parser, metavar='output.mdtm',
                     help='where to store preprocessed annotation in '
                          'MDTM format')

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
    
msg = "(pickle-)dump preprocessed similarity matrix." + clicommon.msgURI()
fparser.add_argument('--dump', type=output_fparser, default=SUPPRESS,
                     metavar='matrix.pkl', help=msg)

from pyannote.parser.cvhci.smallfacetracks import SMALLFACETRACKSLSTParser
def tracks_fparser(path):
    return SMALLFACETRACKSLSTParser().read(path)
    
fparser.add_argument('--small-tracks', type=tracks_fparser, default=SUPPRESS,
                     metavar='smallfaces_trackslist.txt', 
                     help='remove small-faces tracks in provided list')

fparser.add_argument('--no-distance', action='store_true',
                     help='remove tracks for which no distance is available')


try:
    args = argparser.parse_args()
except Exception, e:
    sys.exit(e)

args.func(args)
