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
import networkx as nx

from argparse import ArgumentParser, SUPPRESS
from pyannote import clicommon
from pyannote.parser import AnnotationParser

argparser = ArgumentParser(parents=[clicommon.parser],
                           description='Multimodal Prob Graph Shortest Path')

def input_parser(path):
    
    def load_mpg(uri):
        return nx.read_gpickle(clicommon.replaceURI(path, uri))
    
    return load_mpg
    
msg = 'path to input Multimodal Probability Graph. ' + clicommon.msgURI()
argparser.add_argument('input', type=input_parser, metavar='mpg.pkl', help=msg)

def output_parser(path):
    try:
       with open(path) as f: pass
    except IOError as e:
        writer, extension = AnnotationParser.guess(path)
        return writer(), open(path, 'w')
    raise IOError('ERROR: output file %s already exists. Delete it first.\n' % path)

argparser.add_argument('output', type=output_parser, metavar='output.mdtm',
                       help='path to where to store the output')


ss = argparser.add_mutually_exclusive_group()
ss.add_argument('--ss', action='store_const', dest='ss',
                     const=True, default=True,
                     help='keep speaker diarization edges')
ss.add_argument('--no-ss', action='store_const', dest='ss',
                     const=False, default=True,
                     help='remove speaker diarization edges')

hh = argparser.add_mutually_exclusive_group()
hh.add_argument('--hh', action='store_const', dest='hh',
                     const=True, default=True,
                     help='keep face clustering edges')
hh.add_argument('--no-hh', action='store_const', dest='hh',
                     const=False, default=True,
                     help='remove face clustering edges')


si = argparser.add_mutually_exclusive_group()
si.add_argument('--si', action='store_const', dest='si',
                     const=True, default=True,
                     help='keep speaker recognition edges')
si.add_argument('--no-si', action='store_const', dest='si',
                     const=False, default=True,
                     help='remove speaker recognition edges')

hi = argparser.add_mutually_exclusive_group()
hi.add_argument('--hi', action='store_const', dest='hi',
                     const=True, default=True,
                     help='keep face recognition edges')
hi.add_argument('--no-hi', action='store_const', dest='hi',
                     const=False, default=True,
                     help='remove face recognition edges')

sh = argparser.add_mutually_exclusive_group()
sh.add_argument('--sh', action='store_const', dest='sh',
                     const=True, default=True,
                     help='keep speaker/face edges')
sh.add_argument('--no-sh', action='store_const', dest='sh',
                     const=False, default=True,
                     help='remove speaker/face edges')

sw = argparser.add_mutually_exclusive_group()
sw.add_argument('--sw', action='store_const', dest='sw',
                     const=True, default=True,
                     help='keep speaker/written edges')
sw.add_argument('--no-sw', action='store_const', dest='sw',
                     const=False, default=True,
                     help='remove speaker/written edges')

hw = argparser.add_mutually_exclusive_group()
hw.add_argument('--hw', action='store_const', dest='hw',
                     const=True, default=True,
                     help='keep face/written edges')
hw.add_argument('--no-hw', action='store_const', dest='hw',
                     const=False, default=True,
                     help='remove face/written edges')

try:
    args = argparser.parse_args()
except IOError as e:
    sys.exit(e)


if not hasattr(args, 'uris'):
    raise IOError('missing list of resources (--uris)')

from pyannote.algorithm.mpg.node import IdentityNode, TrackNode
from pyannote.algorithm.mpg.util import complete_mpg
from pyannote.base.annotation import Annotation
import time


writer, f = args.output

for u, uri in enumerate(args.uris):
    
    if args.verbose:
        sys.stdout.write('[%d/%d] %s\n' % (u+1, len(args.uris), uri))
        sys.stdout.flush()
    
    # load Multimodal Probability Graph
    mpg = args.input(uri)
    
    if args.ss == False:
        mpg.remove_diarization_edges('speaker')
    
    if args.hh == False:
        mpg.remove_diarization_edges('head')
    
    if args.si == False:
        mpg.remove_recognition_edges('speaker')
    
    if args.hi == False:
        mpg.remove_recognition_edges('head')
    
    if args.sh == False:
        mpg.remove_crossmodal_edges('speaker', 'head')
    
    if args.sw == False:
        mpg.remove_crossmodal_edges('speaker', 'written')
    
    if args.hw == False:
        mpg.remove_crossmodal_edges('head', 'written')
    
    # make it a complete graph
    if args.verbose:
        sys.stdout.write('    computing shortest paths\n')
        sys.stdout.flush()
    
    C = mpg.complete()  
    
    annotations = C.to_annotation()
    
    writer.comment(uri, f=f)
    
    for uri, modality in annotations:
        writer.write(annotations[uri, modality], f=f)

f.close()
