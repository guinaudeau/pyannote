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
    
    # make it a complete graph
    C = mpg.complete()  
    
    annotations = C.to_annotation()
    
    writer.comment(uri, f=f)
    
    for uri, modality in annotations:
        writer.write(annotations[uri, modality], f=f)

f.close()
